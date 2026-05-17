# HTTP-project---Networks-and-Communications-II

### User guide step by step

**1. clone the repo**
```
git clone https://github.com/beatrizalbiac/HTTP-project-Networks-and-Communications-II.git
cd HTTP-project-Networks-and-Communications-II
```

**2. create the virtual enviroment and activate it (just if you don't want to download the libraries on your computer)**
```
python -m venv venv
```
*Windows*
```
venv\Scripts\Activate.ps1
```

*MacOS / Linux*
```
source venv/bin/activate
```

**3. Install dependencies**
```
pip install -r requirements.txt
```

**4. Create the .env file**

*Windows CMD*
```
echo API_KEY=1234> .env
echo PORT=8080>> .env
echo HOST=127.0.0.1>>> .env
```
*Powershell*
```
"API_KEY=1234`nPORT=8080`nHOST=127.0.0.1" | Out-File -Encoding utf8 -FilePath .env
```

*MacOS / Linux*
```
echo "API_KEY=1234" > .env
echo "PORT=8080" >> .env
echo "HOST=127.0.0.1" >>> .env
```

You might need to close and re-open the IDE (e.g. Visual Studio) you're using for it to work

**5. Run the server**
```
python server/main.py
```

**6. Run the client (in another terminal)**
```
python client/run_client.py
```
```
python client/gui_client.py
```
