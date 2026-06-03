import g4f

try:
    response = g4f.ChatCompletion.create(
        model=g4f.models.default,
        messages=[{"role": "user", "content": "hello"}],
    )
    print("SUCCESS:", response)
except Exception as e:
    print("ERROR:", e)
