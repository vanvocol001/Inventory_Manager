from fastapi import FastAPI, Request
import uvicorn

from fastapi.responses import HTMLResponse

from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from pydantic import BaseModel, Field
from uuid import UUID

app = FastAPI()

templates = Jinja2Templates(directory='templates')

app.mount(
     '/static',
     StaticFiles(directory=Path(__file__).parent.absolute()/'static'),
     name = 'static'
)

@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse('Homepage.html', context={'request': request})

@app.get('/items/{item}')
async def get_item(item : str):
     return {'item name': item}



class inventoryItem(BaseModel):
     id: UUID
     description: str = Field(min_length=1)

PRODUCTS = []
def create_inventoryItems():
     product1 = inventoryItem(id = 'de296eb3-4f81-4131-a31a-37c449d62c96', description = "coke")

     PRODUCTS.append(product1)

@app.get('/products')
async def getProducts(request: Request):
     create_inventoryItems()
     return templates.TemplateResponse('products.html', context={'request': request, 'result': PRODUCTS})

if __name__ == '__main__':
     uvicorn.run(app)

