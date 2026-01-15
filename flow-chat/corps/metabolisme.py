#!/usr/bin/env python3
"""
METABOLISME — Service FastAPI pour le corps
Expose les fonctions corporelles via API
"""

import asyncio
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
import uvicorn

from . import corps, sang

app = FastAPI(title="Flow Corps", description="Systèmes biologiques")

class DigestRequest(BaseModel):
    data: str

class NourrishRequest(BaseModel):
    concepts: list[str]

@app.get("/health")
async def health():
    """État vital complet"""
    return corps.etat_vital()

@app.post("/digest")
async def digest(req: DigestRequest):
    """Digérer des données"""
    return corps.metaboliser(req.data)

@app.post("/nourrir")
async def nourrir(req: NourrishRequest):
    """Nourrir la flore intestinale"""
    corps.flore.nourrir(req.concepts)
    return {
        'diversite': corps.flore.diversite,
        'probiotiques': corps.flore.probiotiques()
    }

@app.get("/fermenter")
async def fermenter():
    """Générer des connexions créatives"""
    return {
        'connexions': corps.flore.fermenter(),
        'probiotiques': corps.flore.probiotiques()
    }

@app.post("/immuniser")
async def immuniser(text: str):
    """Check immunitaire sur un texte"""
    threats = corps.pus.detecter_infection(text)
    if threats:
        return corps.pus.reagir(threats)
    return {'status': 'sain', 'temperature': corps.pus.temperature}

@app.get("/detox")
async def detox():
    """Lancer un cycle de détoxification"""
    toxines = corps.lymphe.detoxifier()
    return {
        'toxines_eliminees': toxines,
        'circulation': corps.lymphe.circulation_lymphatique()
    }

@app.get("/pulse")
async def pulse():
    """Pouls - état de la circulation"""
    sang.battre()
    return {
        'oxygene': len(sang.oxygene),
        'co2': len(sang.co2),
        'groupe': sang.groupe_sanguin()
    }

# Background task pour la circulation sanguine
@app.on_event("startup")
async def start_circulation():
    asyncio.create_task(sang.circuler())

if __name__ == '__main__':
    uvicorn.run(app, host='127.0.0.1', port=8101)
