import urllib.request

try:
    with urllib.request.urlopen("http://localhost:8000/metrics") as response:
        content = response.read().decode("utf-8")
        print(content[:200])
except Exception as e:
    print(e)
