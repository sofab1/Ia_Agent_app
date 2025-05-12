# --------------- db_service.py ---------------
import psycopg2
from psycopg2 import sql, OperationalError
from typing import Dict, List, Optional, Tuple, Any
from functools import lru_cache
import contextlib
import spacy
import json

nlp = spacy.load("fr_core_news_md")  # Charger une seule fois le modèle

class DatabaseService:
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_db()
        return cls._instance
    
    def _init_db(self):
        self.config = {
            "host": "localhost",
            "database": "sofabi",
            "user": "odoo",
            "password": "root",
            "connect_timeout": 5
        }
    
    @contextlib.contextmanager
    def _get_connection(self):
        """Gestionnaire de connexion sécurisé"""
        conn = None
        try:
            conn = psycopg2.connect(**self.config)
            conn.autocommit = False
            yield conn
        except OperationalError as e:
            raise DatabaseError(f"Connection failed: {str(e)}")
        finally:
            if conn:
                conn.close()
    
    @lru_cache(maxsize=100)
    def get_filtered_schema(self, question: str) -> Dict[str, List[str]]:
        """Récupère le schéma pertinent avec cache intelligent"""
        keywords = self._extract_keywords(question)
        
        print(f"##### Mots-clés extraits : {keywords}")
        if not keywords:
            return {}
            
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                tables = self._find_relevant_tables_from_schema(cur, keywords)
                print(f"##### Tables pertinentes trouvées (schéma + alias) : {tables}")
                schema = {}
                
                for table in tables[:20]:  # Limite à 20 tables max
                    columns = self._get_table_columns(cur, table)
                    schema[table] = columns[:50]  # Limite à 50 colonnes
                
                return schema

    def execute_sql(self, query: str) -> List[Tuple]:
        """Exécute une requête SQL de manière sécurisée"""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                try:
                    cur.execute(query)
                    return cur.fetchall()
                except Exception as e:
                    conn.rollback()
                    raise DatabaseError(f"SQL execution failed: {str(e)}")
                finally:
                    conn.commit()

    def _find_relevant_tables_from_schema(self, cursor, keywords: List[str]) -> List[str]:
        """Trouve les tables pertinentes via le schéma + alias locaux"""
        table_aliases = {
            "commande": ["sale_order"],
            "facture": ["account_move"],
            "paiement": ["account_payment", "payment_transaction"],
            "produit": ["product_product", "product_template"],
            "client": ["res_partner"],
            "utilisateur": ["res_users"],
            "employé": ["hr_employee"],
            "stock": ["stock_picking", "stock_move", "stock_quant"],
            "livraison": ["stock_picking"],
            "achat": ["purchase_order"],
            "article": ["product_template"],
            "avance": ["account_payment"],
            "règlement": ["account_payment"],
            "devis": ["sale_order"],
            
            # === New aliases from schema ===
            "mouvement_stock": ["stock_move", "stock_move_line"],
            "ligne_mouvement": ["stock_move_line"],
            "transfert": ["stock_picking"],
             "groupe_mouvement": ["stock_move_line_groupe"],
            "uom": ["product_uom"],
            "entrepot": ["stock_warehouse"],
            "partenaire": ["res_partner"],
            "commande_client": ["sale_order", "sale_order_line"],
            "commande_fournisseur": ["purchase_order", "purchase_order_line"],
            "produit_template": ["product_template"],
            "produit_composé": ["product_product"],
             "lieu_stockage": ["stock_location"],

            # === Additional aliases based on more detailed schema ===
            "produit_fini": ["product_product"],  # Finished product alias
            "categorie_produit": ["product_category"],  # Product category alias
            "emplacement_stock": ["stock_location"],  # Storage location alias
             "etat_stock": ["stock_inventory", "stock_quant"],  # Stock status alias
            "livraison_en_cours": ["stock_picking"],  # Alias for in-progress deliveries
            "commande_vente": ["sale_order"],  # Sales order alias
            "historique_paiement": ["account_payment", "payment_transaction"],  # Payment history alias
    
        }

        cursor.execute("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public';
        """)
        available_tables = {row[0] for row in cursor.fetchall()}

        relevant = set()

        for word in keywords:
            # Correspondance directe avec les noms de table
            for table in available_tables:
                if word in table:
                    relevant.add(table)

            # Correspondance avec les alias définis
            for alias_table in table_aliases.get(word, []):
                if alias_table in available_tables:
                    relevant.add(alias_table)

        return list(relevant)

    def _get_table_columns(self, cursor, table: str) -> List[str]:
        """Récupère les colonnes d'une table spécifique"""
        cursor.execute("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = %s ORDER BY ordinal_position;
        """, (table,))
        return [row[0] for row in cursor.fetchall()]

    def _extract_keywords(self, text: str) -> List[str]:
        """Extrait les mots-clés significatifs"""
        doc = nlp(text.lower())
        keywords = [
            token.lemma_ for token in doc
            if token.pos_ in {"NOUN", "PROPN", "VERB", "ADJ"} and not token.is_stop
        ]
        return list(set(keywords))  # Évite les doublons


class DatabaseError(Exception):
    pass
