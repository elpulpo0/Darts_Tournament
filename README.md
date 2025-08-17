### Template

## Installation

**Clone this repository**

```bash
git clone https://github.com/Microphyt/Template.git
```

**Create and edit your environnement files**

```sh
cp .env.example .env
```

```sh
cp frontend/.env.example frontend/.env
```

**Create and edit your initial users config file**

```sh
cp backend/modules/api/users/initial_users.yaml.example backend/modules/api/users/initial_users.yaml
```

Open 2 different terminals:

# Backend (in terminal 1)

```bash
cd backend
```

**Create a virtual environnement**

```bash
python -m venv .venv
```

**Connect to the virtual environnement**

```bash
source .venv/Scripts/activate
```

**Upgrade pip and install librairies**

```bash
python.exe -m pip install --upgrade pip
```

```bash
pip install -r requirements.txt
```

**Run the app**

```bash
uvicorn run:app --reload
```

# Frontend (in terminal 2)

```bash
cd frontend
```

**Install dependencies**

```bash
npm install
```

**Run the app**

```bash
npm run dev
```

