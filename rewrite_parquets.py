"""Regrava Parquets no S3 com timestamps limitados a microssegundos."""

import argparse
import io
import os

import boto3
import pyarrow as pa
import pyarrow.parquet as pq
from dotenv import load_dotenv
from tqdm import tqdm


def has_nanosecond_timestamp(schema: pa.Schema) -> bool:
    return any(
        pa.types.is_timestamp(field.type) and field.type.unit == "ns"
        for field in schema
    )


def rewrite_parquet(s3, bucket: str, key: str, dry_run: bool) -> bool:
    """Lê um objeto Parquet e substitui-o somente após gerar o novo conteúdo."""
    source = io.BytesIO(s3.get_object(Bucket=bucket, Key=key)["Body"].read())
    if not has_nanosecond_timestamp(pq.ParquetFile(source).schema_arrow):
        return False

    source.seek(0)
    table = pq.read_table(source)

    target = io.BytesIO()
    pq.write_table(
        table,
        target,
        compression="snappy",
        coerce_timestamps="us",
        allow_truncated_timestamps=True,
    )

    if not dry_run:
        target.seek(0)
        s3.upload_fileobj(target, bucket, key)
    return True


def list_parquet_keys(s3, bucket: str, prefix: str) -> list[str]:
    paginator = s3.get_paginator("list_objects_v2")
    pages = paginator.paginate(Bucket=bucket, Prefix=prefix)
    return [
        item["Key"]
        for page in pages
        for item in page.get("Contents", [])
        if item["Key"].endswith(".parquet")
    ]


def rewrite_prefix(s3, bucket: str, prefix: str, dry_run: bool = False) -> tuple[int, int]:
    """Converte os Parquets do prefixo e retorna (convertidos, total)."""
    keys = list_parquet_keys(s3, bucket, prefix)
    action = "Validando" if dry_run else "Regravando"
    rewritten = 0
    for key in tqdm(keys, desc=action, unit="arquivo"):
        rewritten += rewrite_parquet(s3, bucket, key, dry_run)
    return rewritten, len(keys)


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser()
    parser.add_argument("--bucket", default=os.getenv("AWS_BUCKET_NAME"))
    parser.add_argument("--prefix", default="f1/results/")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if not args.bucket:
        parser.error("Informe --bucket ou defina AWS_BUCKET_NAME no .env.")

    s3 = boto3.client(
        "s3",
        aws_access_key_id=os.getenv("AWS_KEY"),
        aws_secret_access_key=os.getenv("AWS_SECRET_KEY"),
        region_name="us-east-1",
    )
    action = "Validando" if args.dry_run else "Regravando"
    rewritten, total = rewrite_prefix(s3, args.bucket, args.prefix, args.dry_run)

    print(
        f"{action}: {rewritten} convertido(s), {total - rewritten} "
        f"Já compatível(is), {total} arquivo(s) no prefixo "
        f"s3://{args.bucket}/{args.prefix}"
    )


if __name__ == "__main__":
    main()
