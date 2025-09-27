# doubao-seedream-master

Doubao Seedream Plugin for Dify

https://github.com/langgenius/dify-plugin-daemon/releases

```bash
uv pip compile pyproject.toml -o doubao-seedream-master/requirements.txt
```

```bash
mkdir -p difypkg
./dify-plugin-windows-amd64.exe plugin package doubao-seedream-master/ -o difypkg/doubao-seedream-master-0.0.1.difypkg
```