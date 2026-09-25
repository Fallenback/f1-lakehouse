import dotenv
import os
dotenv.load_dotenv()
import boto3
from tqdm import tqdm
import argparse

AWS_KEY = os.getenv("AWS_KEY")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_KEY")
verify = os.getenv("AWS_CA_BUNDLE")

class Sender:

    def __init__(self, bucket_name, bucket_folder):
        self.bucket_name = bucket_name
        self.bucket_folder = bucket_folder
        self.s3 = boto3.client("s3", 
             aws_access_key_id=AWS_KEY, 
             aws_secret_access_key=AWS_SECRET_KEY,
             region_name="us-east-1"
             )
    
    def process_file(self, filename):

        file = filename.split("/")[-1]
        bucket_path = os.path.join(self.bucket_folder, file)

        try:
            self.s3.upload_file(filename, 
                                self.bucket_name, 
                                bucket_path)
            print(f"Arquivo {filename} enviado com sucesso para o bucket {self.bucket_name}/{self.bucket_folder}")
            os.remove(filename)
            return True
        except Exception as e:
            print("Erro:", e)
            return False

    def process_folder(self, folder):
        files = [i for i in os.listdir(folder) if i.endswith(".parquet")]
        for file in tqdm(files):
            self.process_file(os.path.join(folder, file))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--bucket_name", type=str, default="datalake-raw-925645278556-us-east-1-an")
    parser.add_argument("--folder", type=str, default="data")
    parser.add_argument("--bucket_path", type=str, default="f1/results")
    args = parser.parse_args()

    send = Sender(args.bucket_name, args.bucket_path)
    send.process_folder(args.folder)

