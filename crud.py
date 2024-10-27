from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from setting import DATABASE_URL, SECRET_KEY
from models import *
import hashlib
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Dict, Union


def create_engine_and_session():
    engine = create_engine(DATABASE_URL, echo=False)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal


def hash_password(password: str) -> str:
    return hashlib.sha256(f"{password}{SECRET_KEY}".encode()).hexdigest()


def create_history_transaction(
    db_session,
    receiver,
    sender,
    transaction_amount,
    transaction_fee,
    transaction_type,
    receiver_id,
    sender_id,
    devisein,
):
    try:
        # Créer une nouvelle transaction
        new_transaction = TransactionHistory(
            receiver=receiver,
            sender=sender,
            transaction_amount=transaction_amount,
            transaction_fee=transaction_fee,
            transaction_type=transaction_type,
            receiver_id=receiver_id,
            sender_id=sender_id,
            devise=devisein,
        )
        # Ajouter la transaction à la session
        db_session.add(new_transaction)

        # Sauvegarder les changements dans la base de données
        db_session.commit()

        # Vérifier si l'objet a bien été ajouté
        if new_transaction.id is not None:
            return new_transaction, True
        else:
            return None, False
    except Exception as e:
        # En cas d'erreur, effectuer un rollback pour annuler les changements
        db_session.rollback()
        print(f"Erreur lors de la création de la transaction : {e}")
        return None, False


def login(db_session: Session, username: str, password: str):
    try:
        hashed_password = hash_password(password)
        user_security = (
            db_session.query(Security)
            .filter_by(username=username, password=hashed_password)
            .one()
        )
        if user_security:
            check = {
                "type_user": user_security.user_type,
                "user_id": user_security.user_id,
                "status": user_security.status,
            }
            return check
        else:
            return None
    except NoResultFound:
        return None


def getsolde_dh(db_session: Session, id_user: int):
    try:
        accountdh = (
            db_session.query(AccountDH).filter(AccountDH.user_id == id_user).one()
        )
        if not accountdh:
            return {"message": "Aucun compte trouvé pour cet utilisateur."}
        return {"id_card": accountdh.card_id, "balance": accountdh.balance}
    except Exception as e:
        print(f"Erreur lors de la récupération des infos du compte : {e}")
        return None


def getsolde_fcfa(db_session: Session, id_user: int):
    try:
        accountfcfa = (
            db_session.query(AccountFCFA).filter(AccountFCFA.user_id == id_user).one()
        )

        if not accountfcfa:
            return {"message": "Aucun compte trouvé pour cet utilisateur."}

        return {"id_card": accountfcfa.card_id, "balance": accountfcfa.balance}

    except Exception as e:
        print(f"Erreur lors de la récupération des infos du compte : {e}")
        return None


def activate_account(
    db_session: Session, username: str, password: str, activation_code: str
):
    try:
        user_security = db_session.query(Security).filter_by(username=username).one()
        hashed_password = hash_password(password)
        if (
            user_security.password == hashed_password
            and user_security.activation_code == activation_code
        ):
            if not user_security.status:
                user_security.status = True
                db_session.commit()
                return {
                    "message": "Compte activé avec succès",
                    "type_user": user_security.user_type,
                    "user_id": user_security.user_id,
                }
            else:
                return {"message": "Le compte est déjà activé"}
        else:
            return {
                "message": "Informations d'authentification ou code d'activation incorrectes"
            }
    except NoResultFound:
        return {"message": "Nom d'utilisateur non trouvé"}


def envoieargent(
    db_session: Session,
    sender_account_id: str,
    receiver_account_id: str,
    amount: float,
    exchange_rate: float,
):
    try:
        if sender_account_id[:3] == "212":
            sender_account = (
                db_session.query(AccountDH).filter_by(id=sender_account_id).one()
            )
        else:
            sender_account = (
                db_session.query(AccountFCFA).filter_by(id=sender_account_id).one()
            )

        if receiver_account_id[:3] == "212":
            receiver_account = (
                db_session.query(AccountDH).filter_by(id=receiver_account_id).one()
            )
        else:
            receiver_account = (
                db_session.query(AccountFCFA).filter_by(id=receiver_account_id).one()
            )

        if sender_account.balance < amount:
            return {"message": "Solde insuffisant"}

        converted_amount = amount * exchange_rate
        sender_account.balance -= amount
        receiver_account.balance += converted_amount

        transaction = TransactionHistory(
            receiver=receiver_account.user.name,
            sender=sender_account.user.name,
            transaction_amount=amount,
            transaction_fee=0,
            transaction_type="Currency Transfer",
            receiver_id=receiver_account.user_id,
            sender_id=sender_account.user_id,
        )
        db_session.add(transaction)
        db_session.commit()
        return {"message": "Transfert réussi"}
    except NoResultFound:
        return {"message": "Compte expéditeur ou récepteur non trouvé"}


def retraitargent(db_session: Session, account_id: str, amount: float):
    try:
        if account_id[:3] == "212":
            account = db_session.query(AccountDH).filter_by(id=account_id).one()
        else:
            account = db_session.query(AccountFCFA).filter_by(id=account_id).one()

        if account.balance < amount:
            return {"message": "Solde insuffisant"}

        account.balance -= amount

        transaction = TransactionHistory(
            receiver=account.user.name,
            sender=account.user.name,
            transaction_amount=amount,
            transaction_fee=0,
            transaction_type="Withdrawal",
            receiver_id=account.user_id,
            sender_id=account.user_id,
        )
        db_session.add(transaction)
        db_session.commit()
        return {"message": "Retrait réussi"}
    except NoResultFound:
        return {"message": "Compte non trouvé"}


def get_account_info(db_session: Session, username: str, password: str):
    try:
        hashed_password = hash_password(password)
        user_security = (
            db_session.query(Security)
            .filter_by(username=username, password=hashed_password)
            .one()
        )

        if user_security:
            card_id = user_security.user_id
            accountfcfa = (
                db_session.query(AccountFCFA).filter_by(user_id=card_id).one_or_none()
            )
            accountdh = (
                db_session.query(AccountDH).filter_by(user_id=card_id).one_or_none()
            )

            total_balance = 0
            user_id = None

            if accountdh and accountdh.status:
                devise = "MAD"
                total_balance = accountdh.balance
                user_id = accountdh.card_id

            if accountfcfa and accountfcfa.status:
                devise = "FCFA"
                total_balance = accountfcfa.balance
                user_id = accountfcfa.card_id

            return {
                "account_id": user_id,
                "balance": f"{total_balance} {devise}",
                "username": user_security.username,
            }
        else:
            return {"message": "Compte inexistant"}
    except NoResultFound:
        return {"message": "Nom d'utilisateur non trouvé"}


##mobile crud
def activation_account(db: Session, name: str, pswd: str, code: str):
    hashed_password = hash_password(pswd)
    user = (
        db.query(Security).filter_by(username=name, activation_code=code).one_or_none()
    )
    if user is None:
        return {"message": "Activation échouée", "status": False, "password": None}
    else:
        user.activation_code = None
        user.status = True
        user.password = hashed_password
        db.commit()
        return {
            "message": "Activation réussie",
            "status": True,
            "password": hashed_password,
        }


def login_mobile(db: Session, name: str, pswd: str):
    hashed_password = hash_password(pswd)
    user = (
        db.query(Security)
        .filter_by(username=name, password=hashed_password)
        .one_or_none()
    )

    if user is None:
        return {
            "ID_user": None,
            "message": "Login échoué",
            "status": False,
            "password": None,
        }
    else:
        return {
            "ID_user": user.user_id,
            "message": "Login réussi",
            "status": True,
            "password": hashed_password,
        }


def format_with_spaces(number, c):
    # Convertir le nombre en chaîne de caractères s'il ne l'est pas déjà
    number_str = str(number)
    # Découper la chaîne en morceaux de 'c' caractères
    chunks = [number_str[i : i + c] for i in range(0, len(number_str), c)]
    # Joindre les morceaux avec un espace
    formatted_number = " ".join(chunks)
    return formatted_number


def info_account(db: Session, name: str, pswd: str):
    user = db.query(Security).filter_by(username=name, password=pswd).one_or_none()

    if not user:
        return {"numcompte": "null", "solde": "null", "username": "null"}

    # Rechercher les comptes liés à l'utilisateur
    dh = db.query(AccountDH).filter_by(user_id=user.user_id).one_or_none()
    fcfa = db.query(AccountFCFA).filter_by(user_id=user.user_id).one_or_none()

    result = {"username": name}

    # Vérifier et formater les informations du compte DH
    if dh and dh.status:
        result["numcompte"] = format_with_spaces(dh.card_id, 4)
        result["solde"] = f"MAD {dh.balance}"
    else:
        result["numcompte"] = "null"
        result["solde"] = "null"

    # Ajouter les informations du compte FCFA si elles existent
    if fcfa and fcfa.status:
        result["numcompte_fcfa"] = format_with_spaces(fcfa.card_id, 4)
        result["solde_fcfa"] = f"FCFA {fcfa.balance}"
    else:
        result["numcompte_fcfa"] = "null"
        result["solde_fcfa"] = "null"

    return result


def get_all_user_transactions(
    db: Session, name: str, password: str
) -> Union[List[Dict[str, str]], Dict[str, str]]:
    try:
        # Récupération de l'utilisateur
        user = (
            db.query(Security).filter_by(username=name, password=password).one_or_none()
        )
        if not user:
            raise ValueError(
                "Échec d'importation : utilisateur non trouvé ou mot de passe incorrect."
            )

        # Récupération des transactions liées à l'utilisateur, soit comme receveur soit comme expéditeur
        transactions = (
            db.query(TransactionHistory)
            .filter(
                (TransactionHistory.receiver_id == user.user_id)
                | (TransactionHistory.sender_id == user.user_id)
            )
            .all()
        )

        # Formatage des résultats
        return [
            {
                "idstatus": item.transaction_type,
                "solde": str(item.transaction_amount),
                "devise": item.devise,
                "date": str(item.transaction_date.isoformat()[:19].replace("T", " ")),
                "name": item.receiver,
            }
            for item in transactions
        ][::-1]

    except SQLAlchemyError as e:
        print(f"Erreur lors de la récupération des transactions : {e}")
        return {"message": "Erreur lors de la récupération des transactions."}


def withdraw_from_mobile_account(
    db: Session, agent_code: str, amount_str: str, username: str, password: str
) -> dict:
    psword = hash_password(password)
    try:
        # Convert amount to float and handle potential conversion errors
        amount = float(amount_str)
    except ValueError:
        return {"status": False, "error": "Invalid amount format"}

    # Fetch user with provided username and password
    user = (
        db.query(Security).filter_by(username=username, password=psword).one_or_none()
    )
    if not user:
        return {"status": False, "error": "Invalid username or password"}

    # Fetch user accounts
    account_mad = db.query(AccountDH).filter_by(user_id=user.user_id).one_or_none()
    account_cfa = db.query(AccountFCFA).filter_by(user_id=user.user_id).one_or_none()

    # Determine if the user has a valid account
    if not (account_mad and account_mad.status) and not (
        account_cfa and account_cfa.status
    ):
        return {"status": False, "error": "No valid account found"}

    # Apply a 10% fee to the amount
    fee_amount = 0.10 * amount
    total_amount = amount + fee_amount

    # Check if the user has sufficient balance and deduct the amount
    currency = None
    if account_mad and account_mad.status:
        if account_mad.balance < total_amount:
            return {"status": False, "error": "Insufficient balance in MAD account"}
        account_mad.balance -= total_amount
        currency = "MAD"
    elif account_cfa and account_cfa.status:
        if account_cfa.balance < total_amount:
            return {"status": False, "error": "Insufficient balance in FCFA account"}
        account_cfa.balance -= total_amount
        currency = "FCFA"
    else:
        return {"status": False, "error": "No active account found"}

    # Process agent payment based on the agent code
    if agent_code[-3:] == "212" or agent_code[:3] == "212":
        agent_account = db.query(AccountDH).filter_by(card_id=agent_code).one_or_none()
        if not agent_account:
            return {"status": False, "error": "Invalid agent code for MAD account"}

        if currency == "MAD":
            agent_account.balance += amount
        else:
            agent_account.balance += amount / 60
    else:
        agent_account = (
            db.query(AccountFCFA).filter_by(card_id=agent_code).one_or_none()
        )
        if not agent_account:
            return {"status": False, "error": "Invalid agent code for FCFA account"}

        if currency == "FCFA":
            agent_account.balance += amount
        else:
            agent_account.balance += amount * 60

    # Create transaction history
    receiver = db.query(Security).filter_by(user_id=agent_account.user_id).one_or_none()
    if receiver:
        create_history_transaction(
            db,
            receiver.username,
            username,
            amount,
            fee_amount,
            "retrait",
            agent_account.user_id,
            user.user_id,
            currency,
        )
    else:
        return {"status": False, "error": "Receiver information not found"}

    # Commit the transaction for agent's account
    db.commit()
    return {"status": True}


def checkinfotransaction(
    db: Session, code: str, montant: str, user: str, pswd: str, transact: str
) -> Dict[str, Union[str, bool]]:

    # Hash the password
    psword = hash_password(pswd)

    try:
        # Convert amount to float and handle potential conversion errors
        amount = float(montant)
    except ValueError:
        return {
            "net": "null",
            "status": False,
            "frais": "null",
            "recepteur": "null",
            "numtransaction": "null",
        }

    # Authenticate user
    userE = db.query(Security).filter_by(username=user, password=psword).one_or_none()

    if not userE:
        return {
            "net": "null",
            "status": False,
            "frais": "null",
            "recepteur": "null",
            "numtransaction": "null",
        }

    # Fetch user accounts
    account_mad = db.query(AccountDH).filter_by(user_id=userE.user_id).one_or_none()
    account_cfa = db.query(AccountFCFA).filter_by(user_id=userE.user_id).one_or_none()

    if not account_mad and not account_cfa:
        return {
            "net": "null",
            "status": False,
            "frais": "null",
            "recepteur": "null",
            "numtransaction": "null",
        }

    # Determine the fee currency
    if account_mad and account_mad.status:
        devise_frais = "MAD"
    elif account_cfa and account_cfa.status:
        devise_frais = "FCFA"
    else:
        devise_frais = "null"

    # Calculate the fee based on transaction type
    if transact == "retrait":
        fee_amount = 0.1 * amount
    else:
        fee_amount = 0.0

    # Determine account type based on code and fetch the recipient's account
    if code[-3:] == "212" or code[:3] == "212":
        account = db.query(AccountDH).filter_by(card_id=code).one_or_none()
        devise = "MAD"
        if code[:3] == "212":
            codeR = db.query(User).filter_by(id=account.user_id).one_or_none()
            code = f"{codeR.name} {codeR.firstname}" if codeR else "Unknown"
    elif code[-3:] == "241" or code[:3] == "241":
        account = db.query(AccountFCFA).filter_by(user_id=userE.user_id).one_or_none()
        devise = "FCFA"
        if code[:3] == "241":
            codeR = db.query(User).filter_by(id=account.user_id).one_or_none()
            code = f"{codeR.name} {codeR.firstname}" if codeR else "Unknown"
    else:
        return {
            "net": "null",
            "status": False,
            "frais": "null",
            "recepteur": "null",
            "numtransaction": "null",
        }

    # Check if the recipient's account exists
    if not account:
        return {
            "net": "null",
            "status": False,
            "frais": "null",
            "recepteur": "null",
            "numtransaction": "null",
        }

    # Return the transaction details
    return {
        "net": f"{amount:.2f} {devise}",
        "status": True,
        "frais": f"{fee_amount:.2f} {devise_frais}",
        "recepteur": code,
        "numtransaction": "17082024",
    }


def from_mobile_account_envoie(
    db: Session,
    recepteurID: str,
    emetteurName: str,
    emetteurPassword: str,
    montant: str,
) -> dict:
    try:
        # Séparation du nom et du prénom du recepteur
        last_name, first_name = recepteurID.split(" ")
    except ValueError:
        return {
            "status": False,
            "error": "Invalid recepteurID format. Expected 'lastname firstname'",
        }

    # Recherche de l'utilisateur recepteur
    userR = db.query(User).filter_by(name=last_name, firstname=first_name).one_or_none()
    if not userR:
        return {"status": False, "error": "Recepteur not found"}

    fcfR = db.query(AccountFCFA).filter_by(user_id=userR.id).one_or_none()
    dhR = db.query(AccountDH).filter_by(user_id=userR.id).one_or_none()
    if not fcfR and not dhR:
        return {"status": False, "error": "Recepteur account not found"}

    # Hachage du mot de passe de l'émetteur pour la vérification
    hashed_password = hash_password(emetteurPassword)

    # Recherche de l'utilisateur émetteur
    userE = (
        db.query(Security)
        .filter_by(username=emetteurName, password=hashed_password)
        .one_or_none()
    )
    if not userE:
        return {"status": False, "error": "Invalid emetteur credentials"}

    fcfE = db.query(AccountFCFA).filter_by(user_id=userE.user_id).one_or_none()
    dhE = db.query(AccountDH).filter_by(user_id=userE.user_id).one_or_none()
    if not fcfE and not dhE:
        return {"status": False, "error": "Emetteur account not found"}

    if dhE and dhR:
        currency = "MAD"
        if envoiedh_to_dh(db, userE.user_id, userR.id, float(montant)):
            etat = create_history_transaction(
                db,
                last_name,
                emetteurName,
                float(montant),
                0,
                "envoie",
                userR.id,
                userE.user_id,
                currency,
            )[1]
    elif fcfE and fcfR:
        currency = "FCFA"
        if envoiefcfa_to_fcfa(db, userE.user_id, userR.id, float(montant)):
            etat = create_history_transaction(
                db,
                last_name,
                emetteurName,
                float(montant),
                0,
                "envoie",
                userR.id,
                userE.user_id,
                currency,
            )[1]
    else:
        return {
            "status": False,
            "error": "No matching currency accounts between emetteur and recepteur",
        }

    return {"status": etat}


def DH_Agent_Retrait(
    db: Session, codeAgent: str, emetteurName: str, emetteurPassword: str, Montant: str
) -> dict:
    # Recherche de l'utilisateur recepteur
    agent = db.query(AccountDH).filter_by(card_id=codeAgent).one_or_none()
    if not agent:
        return {"status": False, "error": "Recepteur not found"}
    # Hachage du mot de passe de l'émetteur pour la vérification
    hashed_password = hash_password(emetteurPassword)

    # Recherche de l'utilisateur émetteur
    userE = (
        db.query(Security)
        .filter_by(username=emetteurName, password=hashed_password)
        .one_or_none()
    )
    if not userE:
        return {"status": False, "error": "Invalid emetteur credentials"}

    if envoiedh_to_dh(db, userE.user_id, agent.user_id, float(Montant)):
        status = True
    else:
        status = False
    create_history_transaction(
        db,
        codeAgent,
        emetteurName,
        float(Montant),
        float(Montant) * 0.1,
        "retrait",
        agent.user_id,
        userE.user_id,
        "MAD",
    )
    return {"status": status}


def retraitDH(db: Session, user_id: int, montant: float) -> bool:
    try:
        user = db.query(AccountDH).filter(AccountDH.user_id == user_id).one_or_none()
        if (
            user is None or user.balance < montant
        ):  # Check if the user has enough balance
            return False
        user.balance -= montant
        db.commit()
        return True
    except SQLAlchemyError:
        db.rollback()
        return False


def DepotDH(db: Session, user_id: int, montant: float) -> bool:
    try:
        user = db.query(AccountDH).filter(AccountDH.user_id == user_id).one_or_none()
        if user is None:
            return False
        user.balance += montant
        db.commit()
        return True
    except SQLAlchemyError:
        db.rollback()
        return False


def verifysolde(db: Session, userid: int, montant: float) -> bool:
    user = db.query(AccountDH).filter(AccountDH.user_id == userid).one_or_none()
    if user is None or user.balance < montant:
        return False
    return True


def envoiedh_to_dh(db: Session, IDE: int, IDR: int, Montant: float) -> bool:
    if verifysolde(db, IDE, Montant):
        if retraitDH(db, IDE, Montant) and DepotDH(db, IDR, Montant):
            return True
    return False


def FCFA_Agent_Retrait(
    db: Session, codeAgent: str, emetteurName: str, emetteurPassword: str, Montant: str
) -> dict:
    # Recherche de l'utilisateur recepteur
    agent = db.query(AccountFCFA).filter_by(card_id=codeAgent).one_or_none()
    if not agent:
        return {"status": False, "error": "Recepteur not found"}
    # Hachage du mot de passe de l'émetteur pour la vérification
    hashed_password = hash_password(emetteurPassword)

    # Recherche de l'utilisateur émetteur
    userE = (
        db.query(Security)
        .filter_by(username=emetteurName, password=hashed_password)
        .one_or_none()
    )
    if not userE:
        return {"status": False, "error": "Invalid emetteur credentials"}

    if envoiefcfa_to_fcfa(db, userE.user_id, agent.user_id, float(Montant)):
        status = True
    else:
        status = False
    return {"status": status}


def retraitFCFA(db: Session, user_id: int, montant: float) -> bool:
    try:
        user = (
            db.query(AccountFCFA).filter(AccountFCFA.user_id == user_id).one_or_none()
        )
        if (
            user is None or user.balance < montant
        ):  # Check if the user has enough balance
            return False
        user.balance -= montant
        db.commit()
        return True
    except SQLAlchemyError:
        db.rollback()
        return False


def DepotFCFA(db: Session, user_id: int, montant: float) -> bool:
    try:
        user = (
            db.query(AccountFCFA).filter(AccountFCFA.user_id == user_id).one_or_none()
        )
        if user is None:
            return False
        user.balance += montant
        db.commit()
        return True
    except SQLAlchemyError:
        db.rollback()
        return False


def verifysoldeFCFA(db: Session, userid: int, montant: float) -> bool:
    user = db.query(AccountFCFA).filter(AccountFCFA.user_id == userid).one_or_none()
    if user is None or user.balance < montant:
        return False
    return True


def envoiefcfa_to_fcfa(db: Session, IDE: int, IDR: int, Montant: float) -> bool:
    if verifysoldeFCFA(db, IDE, Montant):
        if retraitFCFA(db, IDE, Montant) and DepotFCFA(db, IDR, Montant):
            return True
    return False


def AgentRetrait(
    db: Session, codeagent: str, montant: str, username: str, code: str
) -> dict:
    try:
        # Validation de l'entrée
        try:
            montant = float(montant)
            if montant <= 0:
                return {
                    "status": False,
                    "message": "Le montant doit être supérieur à zéro.",
                }
        except ValueError:
            return {"status": False, "message": "Le montant est invalide."}

        # Vérification de la longueur du code agent
        if len(codeagent) < 3:
            return {"status": False, "message": "Code agent invalide."}

        # Sélection de la table en fonction du code agent
        if codeagent[-3:] == "212":
            AccountModel = AccountDH
            currency = "MAD"
        elif codeagent[-3:] == "241":
            AccountModel = AccountFCFA
            currency = "FCFA"
        else:
            return {"status": False, "message": "Code agent non reconnu."}

        # Récupération des informations de l'agent et du client
        agent = db.query(AccountModel).filter_by(card_id=codeagent).one_or_none()
        client = (
            db.query(Security)
            .filter_by(username=username, password=hash_password(code))
            .one_or_none()
        )
        infoclient = db.query(User).filter_by(id=client.user_id).one_or_none()
        nameclient = f"{infoclient.name} {infoclient.firstname}"
        if not agent or not client:
            return {"status": False, "message": "Agent ou client non trouvé."}

        account_client = (
            db.query(AccountModel).filter_by(user_id=client.user_id).one_or_none()
        )
        if not account_client:
            return {"status": False, "message": "Compte client non trouvé."}

        # Mise à jour des soldes
        fee_amount = montant * 0.1
        total_debit = montant + (fee_amount)
        if account_client.balance < total_debit:
            return {"status": False, "message": "Solde insuffisant."}

        agent.balance += montant
        account_client.balance -= total_debit
        create_history_transaction(
            db,
            codeagent,
            nameclient,
            montant,
            fee_amount,
            "retrait",
            agent.user_id,
            client.user_id,
            currency,
        )
        # Validation des transactions
        db.commit()
        return {"status": True, "message": "Retrait effectué avec succès."}

    except SQLAlchemyError as e:
        db.rollback()
        return {"status": False, "message": f"Erreur de base de données: {str(e)}"}
    except Exception as e:
        return {"status": False, "message": f"Erreur inattendue: {str(e)}"}


def allcontactsuser(db: Session, user: str, pswd: str):
    # Recherche de l'utilisateur dans la base de données
    user_record = (
        db.query(Security).filter_by(username=user, password=pswd).one_or_none()
    )
    if not user_record:
        raise ValueError("Erreur lors du chargement des informations utilisateur")

    # Recherche des contacts associés à l'utilisateur
    contacts = db.query(Contacts).filter_by(user_id=user_record.user_id).all()
    if not contacts:
        return []  # Retourne une liste vide si aucun contact n'est trouvé

    # Retourne une liste des contacts formatée
    return [{"IDuser": el.IDuser, "name": el.name} for el in contacts]


def rechargeaccount(db: Session, user: str, pswd: str, code: str):
    # Fetch the user record
    user_record = (
        db.query(Security).filter_by(username=user, password=pswd).one_or_none()
    )
    if not user_record:
        return {"status": False, "message": "Invalid username or password"}
    # Fetch the recharge record
    recharge = (
        db.query(Recharges)
        .filter_by(user_id=user_record.user_id, numero=code)
        .one_or_none()
    )
    if not recharge:
        return {"status": False, "message": "Invalid code"}
    if recharge.status:
        # Determine the account based on the recharge card type
        if recharge.card[:3] == "212":
            account = (
                db.query(AccountDH).filter_by(user_id=user_record.user_id).one_or_none()
            )
        elif recharge.card[:3] == "241":
            account = (
                db.query(AccountFCFA)
                .filter_by(user_id=user_record.user_id)
                .one_or_none()
            )
        # Update the account balance
        if account:
            account.balance += recharge.solde
            recharge.status = False
        else:
            return {"status": False, "message": "Account not found"}
    else:
        return {"status": False, "message": "Code dejà utilisé"}
    # Commit the transaction
    db.commit()
    return {"status": True, "message": "Recharge effectuée avec succès"}


def add_contact(db: Session, username: str, pswd: str, IDuser: str, name: str):
    # Fetch the user record
    user_record = (
        db.query(Security).filter_by(username=username, password=pswd).one_or_none()
    )
    if not user_record:
        return {"status": False, "message": "Compte non pris en charge"}
    # Create a new contact instance
    new_contact = Contacts(IDuser=IDuser, name=name, user_id=user_record.user_id)
    # Add the new contact to the session
    db.add(new_contact)
    # Commit the transaction to save the new contact to the database
    db.commit()
    # Refresh the session to get the new contact's ID (if needed)
    db.refresh(new_contact)
    return {"status": True, "message": "Contact ajouté avec succès"}
