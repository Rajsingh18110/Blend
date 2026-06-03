import g4f

try:
    response = g4f.ChatCompletion.create(
        model=g4f.models.gpt_4o_mini,
        provider=g4f.Provider.DDGS,
        messages=[{"role": "user", "content": "hello"}],
    )
    print("DDGS:", response)
except Exception as e:
    print("DDGS ERROR:", e)

try:
    response = g4f.ChatCompletion.create(
        model=g4f.models.gpt_4o_mini,
        provider=g4f.Provider.PollinationsAI,
        messages=[{"role": "user", "content": "hello"}],
    )
    print("POLLINATIONS:", response)
except Exception as e:
    print("POLL ERROR:", e)
