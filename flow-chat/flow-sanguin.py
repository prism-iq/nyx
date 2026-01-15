#!/usr/bin/env python3
"""
FLOW SANGUIN - Système circulatoire métabolique
Collecte continue d'informations pour nourrir Flow
"""

import asyncio
import aiohttp
import feedparser
import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FlowSanguin:
    def __init__(self):
        self.db_path = "/opt/flow-chat/adn/circulation.db"
        self.sources = {
            'arxiv_bio': 'http://export.arxiv.org/rss/q-bio',
            'arxiv_neuro': 'http://export.arxiv.org/rss/q-bio.NC', 
            'pubmed_consciousness': 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/erss.cgi?rss_guid=1tHuYZKgLuTYSX8-ktQAdKCuVfzW5KXKh_QF5u9HNvBGzRGtoe',
            'nature_neuro': 'https://feeds.nature.com/nn/rss/current',
            'science_daily': 'https://www.sciencedaily.com/rss/mind_brain.xml'
        }
        self.init_db()
    
    def init_db(self):
        """Initialise la base de circulation"""
        conn = sqlite3.connect(self.db_path)
        conn.execute('''
            CREATE TABLE IF NOT EXISTS nutriments (
                id INTEGER PRIMARY KEY,
                source TEXT,
                title TEXT,
                url TEXT,
                content TEXT,
                keywords TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                digested BOOLEAN DEFAULT FALSE
            )
        ''')
        conn.commit()
        conn.close()
        
    async def collecter_source(self, session, nom, url):
        """Collecte une source RSS/API"""
        try:
            async with session.get(url, timeout=30) as response:
                if response.status == 200:
                    content = await response.text()
                    return self.parser_feed(nom, content)
        except Exception as e:
            logger.error(f"Erreur collecte {nom}: {e}")
            return []
    
    def parser_feed(self, source, content):
        """Parse un feed RSS"""
        feed = feedparser.parse(content)
        items = []
        
        for entry in feed.entries[:5]:  # 5 derniers items
            item = {
                'source': source,
                'title': entry.get('title', ''),
                'url': entry.get('link', ''),
                'content': entry.get('summary', ''),
                'keywords': self.extraire_keywords(entry.get('title', '') + ' ' + entry.get('summary', ''))
            }
            items.append(item)
            
        return items
    
    def extraire_keywords(self, text):
        """Extrait des mots-clés pertinents"""
        keywords_cibles = [
            'consciousness', 'bioelectric', 'morphogenesis', 'network',
            'quantum', 'coherence', 'microtubule', 'prediction', 'emergence',
            'levin', 'penrose', 'hameroff', 'friston', 'entropy'
        ]
        
        text_lower = text.lower()
        found = [kw for kw in keywords_cibles if kw in text_lower]
        return ','.join(found)
    
    def stocker_nutriments(self, items):
        """Stocke les nutriments en base"""
        conn = sqlite3.connect(self.db_path)
        
        for item in items:
            # Évite les doublons
            existing = conn.execute(
                'SELECT id FROM nutriments WHERE url = ?', 
                (item['url'],)
            ).fetchone()
            
            if not existing:
                conn.execute('''
                    INSERT INTO nutriments (source, title, url, content, keywords)
                    VALUES (?, ?, ?, ?, ?)
                ''', (item['source'], item['title'], item['url'], item['content'], item['keywords']))
        
        conn.commit()
        conn.close()
    
    async def cycle_circulation(self):
        """Un cycle de circulation complète"""
        logger.info("🩸 Cycle circulation démarré")
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            for nom, url in self.sources.items():
                tasks.append(self.collecter_source(session, nom, url))
            
            resultats = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Traite les résultats
            total_items = 0
            for items in resultats:
                if isinstance(items, list):
                    self.stocker_nutriments(items)
                    total_items += len(items)
            
            logger.info(f"🩸 Collecté {total_items} nutriments")
            
            # Nettoie les vieux nutriments (> 7 jours)
            self.nettoyer_vieux_nutriments()
    
    def nettoyer_vieux_nutriments(self):
        """Nettoie les nutriments de plus de 7 jours"""
        conn = sqlite3.connect(self.db_path)
        cutoff = datetime.now() - timedelta(days=7)
        conn.execute('DELETE FROM nutriments WHERE timestamp < ?', (cutoff,))
        conn.commit()
        conn.close()
    
    def get_nutriments_frais(self, limit=10):
        """Récupère les nutriments les plus frais"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute('''
            SELECT title, url, content, keywords, timestamp 
            FROM nutriments 
            WHERE digested = FALSE 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (limit,))
        
        items = cursor.fetchall()
        conn.close()
        return items
    
    async def circulation_continue(self):
        """Circulation continue - daemon principal"""
        logger.info("🩸 Système circulatoire démarré")
        
        while True:
            try:
                await self.cycle_circulation()
                # Cycle toutes les 10 minutes
                await asyncio.sleep(600)
                
            except Exception as e:
                logger.error(f"Erreur circulation: {e}")
                await asyncio.sleep(60)  # Retry dans 1 min

if __name__ == "__main__":
    sanguin = FlowSanguin()
    asyncio.run(sanguin.circulation_continue())