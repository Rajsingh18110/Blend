import g4f

try:
    response = g4f.ChatCompletion.create(
        model=g4f.models.gpt_4o,
        provider=g4f.Provider.Blackbox,
        messages=[{"role": "user", "content": "hi"}],
    )
    print("BLACKBOX:", response)
except Exception as e:
    print("BLACKBOX ERROR:", e)

try:
    response = g4f.ChatCompletion.create(
        model=g4f.models.gpt_4o_mini,
        provider=g4f.Provider.DDG,
        messages=[{"role": "user", "content": "hi"}],
    )
    print("DDG:", response)
except Exception as e:
    print("DDG ERROR:", e)
