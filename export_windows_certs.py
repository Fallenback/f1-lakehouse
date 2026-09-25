"""Exporta os certificados raiz confiáveis do Windows para a pasta certs/.

A rede corporativa faz inspeção de HTTPS: o proxy reassina o tráfego com um
certificado próprio, que existe no repositório de certificados do Windows mas
não na imagem Linux. Sem esses certificados, qualquer chamada à AWS ou download
dentro do container falha na validação SSL.

Este script grava um arquivo .crt por certificado em certs/, que o Dockerfile
copia para /usr/local/share/ca-certificates/ e registra com update-ca-certificates.
A verificação SSL continua ligada dentro do container.

Uso:
    python export_windows_certs.py
    python export_windows_certs.py --extra C:\\certs\\unimedsc-ca.pem
"""

import argparse
import base64
import os
import re
import shutil
import ssl
import sys

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "certs")

# Repositórios do Windows que contêm as âncoras de confiança usadas pelo proxy.
STORES = ["ROOT", "CA"]

# Só interessam os certificados válidos para autenticação de servidor TLS.
SERVER_AUTH_OID = "1.3.6.1.5.5.7.3.1"

PEM_BLOCK = re.compile(
    rb"-----BEGIN CERTIFICATE-----.+?-----END CERTIFICATE-----", re.DOTALL
)


def to_pem(der_bytes):
    body = base64.b64encode(der_bytes).decode("ascii")
    lines = [body[i:i + 64] for i in range(0, len(body), 64)]
    return "-----BEGIN CERTIFICATE-----\n{}\n-----END CERTIFICATE-----\n".format(
        "\n".join(lines)
    )


def trusted_for_server_auth(trust):
    # trust é True quando o certificado vale para qualquer propósito,
    # ou um conjunto de OIDs quando o uso é restrito.
    return trust is True or (isinstance(trust, (set, frozenset)) and SERVER_AUTH_OID in trust)


def collect_from_windows_stores():
    if not hasattr(ssl, "enum_certificates"):
        sys.exit("ssl.enum_certificates não existe: rode este script no Windows.")

    pems = []
    for store in STORES:
        try:
            certs = ssl.enum_certificates(store)
        except Exception as err:  # repositório ausente ou sem permissão
            print("aviso: não consegui ler o repositório {}: {}".format(store, err))
            continue

        found = 0
        for der_bytes, encoding, trust in certs:
            if encoding != "x509_asn":
                continue
            if not trusted_for_server_auth(trust):
                continue
            pems.append(to_pem(der_bytes))
            found += 1
        print("repositório {}: {} certificados".format(store, found))

    return pems


def collect_from_files(paths):
    pems = []
    for path in paths:
        if not os.path.exists(path):
            sys.exit("arquivo extra não encontrado: {}".format(path))
        with open(path, "rb") as fh:
            content = fh.read()
        blocks = PEM_BLOCK.findall(content)
        if not blocks:
            sys.exit("nenhum certificado PEM encontrado em {}".format(path))
        for block in blocks:
            pems.append(block.decode("ascii") + "\n")
        print("arquivo {}: {} certificados".format(path, len(blocks)))
    return pems


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--extra",
        nargs="+",
        default=[],
        help="arquivos .pem/.crt adicionais para incluir no bundle",
    )
    args = parser.parse_args()

    pems = collect_from_windows_stores() + collect_from_files(args.extra)

    # Deduplica mantendo a ordem: o mesmo certificado costuma aparecer em ROOT e CA.
    unique = list(dict.fromkeys(pems))

    if not unique:
        sys.exit("nenhum certificado exportado, abortando.")

    if os.path.isdir(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR)

    # update-ca-certificates exige um certificado por arquivo, com extensão .crt.
    for index, pem in enumerate(unique):
        filename = os.path.join(OUTPUT_DIR, "windows-{:03d}.crt".format(index))
        with open(filename, "w") as fh:
            fh.write(pem)

    print("\n{} certificados gravados em {}".format(len(unique), OUTPUT_DIR))


if __name__ == "__main__":
    main()
