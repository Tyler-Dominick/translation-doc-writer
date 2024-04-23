from flask import Flask
from flask_sqlalchemy import SQLAlchemy
# import psycopg2

POSTGRES_URL="postgresql://default:wEa1GZcD3Llh@ep-misty-voice-a4o0ylno-pooler.us-east-1.aws.neon.tech:5432/verceldb?sslmode=require"
POSTGRES_PRISMA_URL="postgres://default:wEa1GZcD3Llh@ep-misty-voice-a4o0ylno-pooler.us-east-1.aws.neon.tech:5432/verceldb?sslmode=require&pgbouncer=true&connect_timeout=15"
POSTGRES_URL_NO_SSL="postgres://default:wEa1GZcD3Llh@ep-misty-voice-a4o0ylno-pooler.us-east-1.aws.neon.tech:5432/verceldb"
POSTGRES_URL_NON_POOLING="postgres://default:wEa1GZcD3Llh@ep-misty-voice-a4o0ylno.us-east-1.aws.neon.tech:5432/verceldb?sslmode=require"
POSTGRES_USER="default"
POSTGRES_HOST="ep-misty-voice-a4o0ylno-pooler.us-east-1.aws.neon.tech"
POSTGRES_PASSWORD="wEa1GZcD3Llh"
POSTGRES_DATABASE="verceldb"

# con = psycopg2.connect(database=POSTGRES_DATABASE, host= POSTGRES_HOST, user=POSTGRES_USER, password=POSTGRES_PASSWORD)

# cursor = con.cursor()

app = Flask(__name__)
app.config['SECRET_KEY']='e1fea3259a0b90aa14bfbeebb6b8a25e'
app.config['SQLALCHEMY_DATABASE_URI'] = POSTGRES_URL
db = SQLAlchemy(app)

from webtranslator import routes