from fastapi import FastAPI, HTTPException, Query, Request, Depends  # type: ignore
from fastapi.responses import JSONResponse  # type: ignore
from pydantic import BaseModel  # type: ignore
from sqlalchemy.orm import Session as DBSession
import uvicorn  # type: ignore
from crud import *  
from typing import List

# Initialise l'application FastAPI
app = FastAPI()

# Crée la session pour la base de données
SessionLocal = create_engine_and_session()  # type: ignore

# Dépendance pour récupérer la session de base de données
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

## Partie mobile API
class Transaction(BaseModel):
    idstatus: str
    solde: str  # Tu peux garder "str" si c'est bien une chaîne
    devise: str
    date: str
    name: str


@app.get("/API/V1/transactions/", response_model=List[Transaction])
async def get_transactions(name: str, pswd: str = Query(...), db: DBSession = Depends(get_db)):
    transaction = get_all_user_transactions(db, name, pswd)
    return JSONResponse(content=transaction)


# Modèle pour l'utilisateur
class InfouserHome(BaseModel):
    numcompte: str
    solde: str
    username: str


@app.get("/API/V1/home/info/user/account/account/", response_model=InfouserHome)
async def get_infouser(name: str, pswd: str = Query(...), db: DBSession = Depends(get_db)):
    infoaccountuser = info_account(db, name, pswd)
    return JSONResponse(content=infoaccountuser)


class ActivationResponse(BaseModel):
    message: str
    status: bool
    password: str


@app.get("/API/V1/activation/account/", response_model=ActivationResponse)
async def activate(name: str, pswd: str, code: str = Query(...), db: DBSession = Depends(get_db)):
    stusactivation = activation_account(db, name, pswd, code)
    return JSONResponse(content=stusactivation)


class LoginResponse(BaseModel):
    status: bool
    message: str
    ID_user: int
    password: str


@app.get("/API/V1/login/user/", response_model=LoginResponse)
async def loginmob(name: str, pswd: str = Query(...), db: DBSession = Depends(get_db)):
    statuslogin = login_mobile(db, name, pswd)
    return JSONResponse(content=statuslogin)


class CheckResponse(BaseModel):
    net: str
    status: bool
    frais: str
    recepteur: str
    numtransaction: str


@app.get("/API/V1/resumtransaction/", response_model=CheckResponse)
async def checkresumetransact(
    code: str, montant: str, user: str, pswd: str = Query(...), db: DBSession = Depends(get_db)
):
    infochesend = checkinfotransaction(db, code, montant, user, pswd, "envoie")
    return JSONResponse(content=infochesend)


class CheckRetraitResponse(BaseModel):
    net: str
    status: bool
    frais: str
    recepteur: str
    numtransaction: str


@app.get("/API/V1/retraitresum/", response_model=CheckRetraitResponse)
async def retraitcheck(code: str, montant: str, user: str, pswd: str = Query(...), db: DBSession = Depends(get_db)):
    infocheckretrai = checkinfotransaction(db, code, montant, user, pswd, "retrait")
    return JSONResponse(content=infocheckretrai)


class EnvoieResponse(BaseModel):
    status: bool


@app.get("/API/V1/envoie/", response_model=EnvoieResponse)
async def activate(
    recepteurID: str,
    emetteurName: str,
    emetteurPassword: str,
    Montant: str = Query(...),
    db: DBSession = Depends(get_db)
):
    statusEnvoiec = from_mobile_account_envoie(
        db, recepteurID, emetteurName, emetteurPassword, Montant
    )
    return JSONResponse(content=statusEnvoiec)


class RetraiResponse(BaseModel):
    status: bool
    message: str


@app.get("/API/V1/retrait/", response_model=RetraiResponse)
async def activate(codeagent: str, montant: str, username: str, code: str = Query(...), db: DBSession = Depends(get_db)):
    statusretrait = AgentRetrait(db, codeagent, montant, username, code)
    return JSONResponse(content=statusretrait)


class RechargeResponse(BaseModel):
    status: bool
    message: str


@app.get("/API/V1/recharge/", response_model=RechargeResponse)
async def recharge(code: str, user: str, pswd: str = Query(...), db: DBSession = Depends(get_db)):
    val = rechargeaccount(db, user, pswd, code)
    return RechargeResponse(**val)


class UseraccountResponse(BaseModel):
    IDuser: str
    name: str


@app.get("/API/V1/getallaccount/", response_model=List[UseraccountResponse])
async def get_allaccount(user: str, pswd: str = Query(...), db: DBSession = Depends(get_db)):
    val = allcontactsuser(db, user, pswd)
    return JSONResponse(content=val)


class ContactCreateRequest(BaseModel):
    username: str
    pswd: str
    IDuser: str
    name: str


@app.post("/API/V1/CreateUser/")
async def create_user(contact: ContactCreateRequest, db: DBSession = Depends(get_db)):
    result = add_contact(
        db, contact.username, contact.pswd, contact.IDuser, contact.name
    )
    if not result["status"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result


#if __name__ == "__main__":
    # Lancer l'application avec Uvicorn
#    uvicorn.run("app:app", host="0.0.0.0", port=8090, reload=True)
