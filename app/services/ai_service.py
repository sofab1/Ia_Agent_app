import requests
import httpx
import asyncio
import re  # Ajout de l'import manquant
from datetime import datetime
from typing import List, Dict, Optional, Any
from app.services.security import SecurityService  # Updated import
from app.services.db_service import DatabaseService, DatabaseError
from app.models.schemas import UserQuery

class AIService:
    def __init__(self):
        self.endpoint = "http://localhost:1234/v1/chat/completions"
        self.default_model = "mistral-7b-instruct"
        
        # Initialiser le service de base de données si nécessaire
        try:
            from app.services.broski_db_service import BroskiDatabaseService
            self.broski_db = BroskiDatabaseService()
        except ImportError:
            print("⚠️ BroskiDatabaseService non disponible, fonctionnalités de journalisation désactivées")
            self.broski_db = None
        
        #mistral-7b-instruct
        #deepseek-r1-distill-qwen-7b
        
        
    async def process_question(self, user_query: Dict[str, Any]) -> Dict[str, Any]:  # signature keeps dict input
        """Orchestre le traitement complet d'une question"""
        try:
            # Vérifier si user_query est déjà un objet UserQuery
            if isinstance(user_query, UserQuery):
                user_obj = user_query
            else:
                # Convertir le dict en objet Pydantic pour un accès aux attributs
                user_obj = UserQuery(**user_query)
                
            print(f"🔍 Début traitement - Question: {user_obj.question[:50]}...")  # Log

            # Détecter le type de question depuis l'objet
            question_type = self._detect_question_type(user_obj.question)
            print(f"🔍 Type détecté: {question_type}")
            print(f"🔍 User is   : {user_obj}")

            # Choisir la méthode en fonction du type
            if question_type == "sql":
                print("🛢️ Début traitement SQL")
                result = await self._handle_sql_query(user_obj)  # Passer l'objet Pydantic
            else:
                print("💬 Début traitement général")
                result = await self._handle_general_query(user_obj)
            
            # Vérifier si self.broski_db existe avant de l'utiliser
            if hasattr(self, 'broski_db'):
                self.broski_db.log_interaction(
                    user_data=user_query if not isinstance(user_query, UserQuery) else user_query.dict(),
                    question=user_obj.question,
                    response=result
                )

            print(f"✅ Traitement réussi - Type: {result.get('type')}")
            return result

        except Exception as e:
            error_msg = f"❌ Erreur lors du traitement: {str(e)}"
            print(error_msg)
            error_result = self._format_error(error_msg, "processing_error")
            
            # Vérifier si self.broski_db existe avant de l'utiliser
            if hasattr(self, 'broski_db'):
                self.broski_db.log_interaction(
                    user_data=user_query if not isinstance(user_query, UserQuery) else user_query.dict(),
                    question=user_obj.question if 'user_obj' in locals() else "Question inconnue",
                    response=error_result
                )
            
            return error_result
        
        
    
 
        
    async def _handle_sql_query(self, user_query: UserQuery) -> Dict[str, Any]:  # Updated signature
        print("######## Reusie here")
        try:
            # 1. Génération SQL
            print("🛢️ Génération SQL déclenchée…")
            gen_result = await self._generate_sql_response(
                user_query.question,  # Updated access
                f"User: {user_query.name} ({user_query.email})"  # Updated context
            )
            print("🛢️ gen_result:", gen_result)
            if "error" in gen_result:
                print("❌ gen_result contient une erreur, on sort :", gen_result["error"])
                return gen_result

            # 2. Validation d'accès statique
            can_access = SecurityService.validate_with_user_list(
                user_query,  # Direct UserQuery
                gen_result["query"],
                gen_result["result"]
            )
            print("🔒 Validation d'accès :", can_access)
            if not can_access:
                error_msg = "🔐 Accès refusé pour votre rôle"
                print(error_msg)
                return {
                    "type": "error",
                    "error": {
                        "message": error_msg,
                        "code": "access_denied",
                        "timestamp": datetime.now().isoformat()
                    }
                }

            # 3. Reformulation et filtrage
            print("💬 Reformulation déclenchée…")
            reformulated = await self._reformulate_response(
                question=user_query.question,  # Updated access
                sql_query=gen_result["query"],
                db_result=gen_result["result"],
                user_role=user_query.role  # Updated access
            )
            print("💬 reformulated:", reformulated)

            # 4. Filtrage
            filtered = SecurityService.filter_content(user_query, reformulated)
            print("🔍 filtered:", filtered)

            return {
                "type": "sql",
                "response": filtered,
                "metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "query_type": "sql"
                }
            }

        except Exception as e:
            print("❗ Exception inattendue dans _handle_sql_query:", str(e))
            return self._format_error(f"Erreur traitement SQL: {e}", "sql_processing")
        
    
    async def _generate_sql_response(self, question: str, context: str = "") -> Dict[str, Any]:
        
        """Génère et exécute une requête SQL"""
        try:
            print("🛢️ Récupération du schéma…")
            schema = DatabaseService().get_filtered_schema(question)
            if not schema:
                return self._format_error("Aucun schéma pertinent trouvé", "schema_error")
            
            messages = [
                {
                    "role": "system",
                          "content": (
                             "Tu es un expert SQL sur Odoo 18. Voici le schéma complet de la base `public`:\n\n"
                                        "```\n"
                             + self._format_schema(schema) +
                             "\n```\n\n"
                             "Réponds **exclusivement** par une requête SQL valide encadrée ainsi :\n"
                           "```sql\nSELECT ...\n```\n"
                            "Ne fournis aucune explication supplémentaire."
                                    )
                               },
                             {"role": "user", "content": question}
                                 ]
            
            print("🤖 Appel à l'IA pour génération SQL…")
            response = await self._call_ai(messages, temperature=0.1, max_tokens=250)
            
            sql = self._extract_sql(response)
            if not sql:
                return self._format_error("Requête SQL invalide générée", "sql_generation")
            
            print("🛢️ Exécution de la requête SQL…")
            result = DatabaseService().execute_sql(sql)
            return {"query": sql, "result": result}
            
        except DatabaseError as e:
            return self._format_error(str(e), "database_error")
        except Exception as e:
            return self._format_error(f"Erreur génération SQL: {str(e)}", "sql_generation")

    async def _call_ai(self, messages: List[Dict], temperature: float, max_tokens: int) -> str:
        """Appel standard à l'API IA"""
        try:
            print(f"🤖 Envoi à l'IA (temp={temperature}, tokens={max_tokens})…")
            async with httpx.AsyncClient(timeout=60) as client:
               response = await client.post(
                     self.endpoint,
                     json={
                        "model": self.default_model,
                        "messages": messages,
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                        "stream": False
                       },
                
                      )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"].strip()
        
        except httpx.RequestError as e:  # ✅ correction ici
            print(f"❌ Erreur réseau: {str(e)}")
            raise AIServiceError(f"Échec appel API IA: {str(e)}")
        except Exception as e:
            print(f"❌ Erreur inattendue: {str(e)}")
            raise AIServiceError(f"Erreur traitement réponse IA: {str(e)}")
        
    
    async def _handle_general_query(self, user_query: UserQuery) -> Dict[str, Any]:  # Updated signature
        """Gère les questions générales non-SQL"""
        try:
            messages = [
                {"role": "system", "content": "Tu es un assistant utile pour répondre à des questions générales."},
                {"role": "user", "content": user_query.question}  # Updated access
            ]

            print("🤖 Envoi de la question à l'IA…")
            ai_response = await self._call_ai(messages, temperature=0.7, max_tokens=500)

            return {
                "type": "general",
                "response": ai_response,
                "metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "query_type": "general"
                }
            }
        except Exception as e:
            error_msg = f"❌ Erreur traitement général: {str(e)}"
            print(error_msg)
            return self._format_error(error_msg, "general_processing")

    def _detect_question_type(self, question: str) -> str:
        sql_triggers = [
            "combien", "liste", "affiche", "montre",
            "sélectionne", "select", "count", "où", "quand"
        ]
        return "sql" if any(trigger in question.lower() for trigger in sql_triggers) else "general"

    def _format_schema(self, schema: Dict[str, List[str]]) -> str:
        return "\n".join(f"{table}({', '.join(cols)})" for table, cols in schema.items())

    def _extract_sql(self, text: str) -> Optional[str]:
        match = re.search(r"```sql\n(.*?)\n```", text, re.DOTALL)
        if match:
            sql_code = match.group(1).strip()
            if any(cmd in sql_code.upper() for cmd in ["SELECT", "INSERT"]):
                return sql_code
        return None

    def _format_error(self, message: str, code: str) -> Dict[str, Any]:
        """Formate une erreur de manière standardisée"""
        return {
            "type": "error",
            "error": {
                "message": message,
                "code": code,
                "timestamp": datetime.now().isoformat()
            }
        }
        
    async def _reformulate_response(
        self,
        question: str,
        sql_query: str,
        db_result: Any,
        user_role: str
    ) -> str:
        """
        Utilise l’IA pour reformuler le résultat SQL
        dans un langage naturel adapté au rôle de l’utilisateur.
        """
        try:
            system_prompt = (
                f"Tu es un assistant expert Odoo. Tu reçois une question, une requête SQL "
                f"et un résultat de base de données. Reformule la réponse de manière naturelle "
                f"et adaptée à un utilisateur ayant le rôle : {user_role}.\n"
                f"Ne montre jamais la requête SQL brute.\n"
                f"Fais une réponse claire et concise adaptée au contexte métier."
            )

            user_prompt = (
                f"Question posée : {question}\n"
                f"Requête SQL exécutée : {sql_query}\n"
                f"Résultat : {db_result}"
            )

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]

            print("💬 Appel à l'IA pour reformulation…")
           
            response = await self._call_ai(messages, temperature=0.5, max_tokens=300)
            return response

        except Exception as e:
            print(f"❌ Erreur IA dans reformulation: {str(e)}")
            # Si échec, fallback vers un affichage brut
            return f"Résultat brut : {db_result}"

      
class AIServiceError(Exception):
    """Exception personnalisée pour les erreurs du service IA"""
    pass
