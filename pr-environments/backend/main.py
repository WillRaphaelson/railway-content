import os
import psycopg2
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

DATABASE_URL = os.environ["DATABASE_URL"]

SEED_TRAINS = [
    ("Acela", "High-speed express on the Northeast Corridor", "#c0392b", "Boston → New York → Washington D.C."),
    ("California Zephyr", "Scenic cross-country route through the Rockies", "#2980b9", "Chicago → Denver → San Francisco"),
    ("Coast Starlight", "Pacific Coast route with ocean and mountain views", "#27ae60", "Los Angeles → Portland → Seattle"),
]

def get_conn():
    return psycopg2.connect(DATABASE_URL)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS trains (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            color TEXT,
            route TEXT NOT NULL
        )
    """)
    cur.execute("SELECT COUNT(*) FROM trains")
    if cur.fetchone()[0] == 0:
        cur.executemany(
            "INSERT INTO trains (name, description, color, route) VALUES (%s, %s, %s, %s)",
            SEED_TRAINS,
        )
    conn.commit()
    cur.close()
    conn.close()

@app.get("/trains")
def list_trains():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, name, description, color, route FROM trains ORDER BY id")
    rows = [
        {"id": r[0], "name": r[1], "description": r[2], "color": r[3], "route": r[4]}
        for r in cur.fetchall()
    ]
    cur.close()
    conn.close()
    return rows

@app.post("/trains")
async def create_train(request: Request):
    body = await request.json()
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO trains (name, description, color, route) VALUES (%s, %s, %s, %s) RETURNING id",
        (body["name"], body.get("description"), body.get("color"), body["route"]),
    )
    train_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return {"id": train_id, **body}
