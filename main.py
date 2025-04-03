import os
import sys

from loguru import logger
from AzApi.AzApi import AzApi
from dotenv import load_dotenv


logger.remove()
logger.add(
    sys.stderr,
    level="TRACE",
    format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
)
load_dotenv()

ORG = os.getenv("ORGANIZATION")
PRO = os.getenv("PROJECT")
REPO = os.getenv("REPOSITORY")
PAT = os.getenv("PAT")

api = AzApi(organization=ORG, project=PRO, token=PAT)
api.repository_name = REPO
x = api.Repo.get_all_branches()
y = api.Repo.get_active_pull_requests()
