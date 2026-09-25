import datetime 
from sender import Sender 
from collect import CollectResults 
from rewrite_parquets import rewrite_prefix
import dotenv 
import os
import boto3

year = datetime.datetime.now().year
dotenv.load_dotenv()
BUCKET_NAME = os.getenv("AWS_BUCKET_NAME")

print("Coletando dados da temporada...")
collect_data = CollectResults([year])
collect_data.process_years()

print("Enviando dados para o bucket...")
sender = Sender(bucket_name=BUCKET_NAME, bucket_folder="f1/results")
sender.process_folder("data/")

print("Garantindo timestamps em microssegundos nos Parquets enviados...")
s3 = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_KEY"),
    aws_secret_access_key=os.getenv("AWS_SECRET_KEY"),
    region_name="us-east-1",
)
rewritten, total = rewrite_prefix(s3, BUCKET_NAME, "f1/results/")
print(f"{rewritten} de {total} Parquet(s) foram regravados.")


