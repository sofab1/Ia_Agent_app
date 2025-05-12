from typing import Any
from app.models.schemas import UserQuery
from typing import Any, List, Dict


class SecurityService:
    
    @staticmethod
    def validate_access(user: UserQuery, sql_query: str, result: Any) -> bool:
        """Valide l'accès selon le rôle et le contenu"""
        role = user.role.lower()
        
        # Règles pour les ouvriers
        if role == "ouvrier":
            forbidden = ["salaire", "rh", "financier", "password"]
            if any(keyword in sql_query.lower() for keyword in forbidden):
                return False
            if any(cmd in sql_query.upper() for cmd in ["DELETE", "UPDATE", "DROP"]):
                return False
        
        return True
    
    @staticmethod
    def filter_content(user: UserQuery, content: Any) -> Any:
        """Filtre les données sensibles selon le rôle"""
        if user.role.lower() == "ouvrier":
            if isinstance(content, str):
                sensitive = ["salaire", "confidentiel"]
                if any(word in content.lower() for word in sensitive):
                    return "[Donnée restreinte]"
            elif isinstance(content, list):
                return [SecurityService.filter_content(user, item) for item in content]
        return content
    
    
    # @staticmethod
    # def filter_content(user: UserQuery, content: Any) -> Any:
    #     """
    #     Filtre ou reformule les données sensibles selon le rôle de l'utilisateur.
    #     """

    #     role = user.role.lower()

    #     def has_sensitive_terms(text: str, terms: List[str]) -> bool:
    #         lower = text.lower()
    #         return any(term in lower for term in terms)

    #     # Ouvrier : masquage fort sur paie et données confidentielles
    #     if role == "worker":
    #         sensitive_terms = ["salaire", "payroll", "confidentiel", "rémunération"]
    #         if isinstance(content, str):
    #             if has_sensitive_terms(content, sensitive_terms):
    #                 return ("[Donnée restreinte] Vous n'avez pas les droits "
    #                         "pour consulter ces informations.")
    #             return content

    #         if isinstance(content, list):
    #             return [SecurityService.filter_content(user, item) for item in content]

    #         if isinstance(content, dict):
    #             return {
    #                 k: SecurityService.filter_content(user, v)
    #                 for k, v in content.items()
    #             }

    #     # Manager : masquage sur termes ultra-sensibles
    #     if role == "manager":
    #         if isinstance(content, str):
    #             if has_sensitive_terms(content, ["secret", "mot de passe", "credentials"]):
    #                 return "[Donnée réservée aux admins]"
    #             return content

    #         if isinstance(content, (list, dict)):
    #             return SecurityService.filter_content(
    #                 user,
    #                 content if isinstance(content, list) else list(content.values())
    #             )

    #     # Guest : ne renvoie que du texte brut
    #     if role in ("guest", "visiteur"):
    #         if isinstance(content, str):
    #             return re.sub(r"`{3}.*?`{3}", "", content, flags=re.DOTALL).strip()
    #         return str(content)

    #     # Par défaut, on ne modifie pas
    #     return content
    
    @staticmethod
    def validate_with_user_list(
        user_query: UserQuery,
        query: str,
        result: List[Dict]
    ) -> bool:
        """
        Valide l'accès en fonction du rôle de l'utilisateur et de la nature 
        de la question, en utilisant une liste statique d'utilisateurs.
        """

        # 1. Liste statique des utilisateurs autorisés
        #    id, email, role, name
        authorized_users = [
            {"id": 1, "email": "alice@company.com",   "role": "worker",  "name": "Alice"},
            {"id": 2, "email": "bob@company.com",     "role": "manager", "name": "Bob"},
            {"id": 3, "email": "charlie@company.com", "role": "guest",   "name": "Charlie"},
            # ajoute ici autant d’entrées que nécessaire…
        ]

        # 2. Vérification : l'utilisateur courant est-il dans cette liste ?
        user_valid = any(
            u["id"]    == user_query.user_id and
            u["email"] == user_query.email and
            u["role"]  == user_query.role
            for u in authorized_users
        )
        if not user_valid:
            print("❌ Utilisateur non reconnu ou rôle invalide.")
            return False

        # 3. Règles par rôle et par contenu de la question
        role = user_query.role.lower()
        question = user_query.question.lower()

        # Règles pour Ouvrier (worker)
        if role == "worker":
            if any(term in question for term in ["salaire", "payroll", "rémunération"]):
                print("🚫 Ouvrier ne peut pas consulter le salaire d'un collègue.")
                return False
            if any(term in question for term in ["état", "process", "fabrication", "produit"]):
                return True
            return True

        # Règles pour Manager
        if role == "manager":
            if any(term in question for term in ["mot de passe", "credentials", "secret"]):
                return False
            return True

        # Règles pour Invité (guest)
        if role in ("guest", "visiteur"):
            if any(sql_op in query.lower() for sql_op in ["select", "insert", "update", "delete"]):
                print("🚫 Invité ne peut pas exécuter de requêtes SQL.")
                return False
            return True

        # Par défaut : refus
        print(f"🚫 Rôle '{user_query.role}' non géré.")
        return False
    
    