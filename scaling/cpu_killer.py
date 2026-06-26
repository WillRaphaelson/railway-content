from fastapi import FastAPI

app = FastAPI()

def burn_cpu(n: int) -> int:
    """Count primes up to n — pure CPU, no I/O."""
    count = 0
    for num in range(2, n):
        if all(num % i != 0 for i in range(2, int(num**0.5) + 1)):
            count += 1
    return count

@app.get("/")
def health():
    return {"status": "ok"}

@app.get("/compute")
def compute(n: int = 80000):
    result = burn_cpu(n)
    return {"primes_found": result, "up_to": n}
