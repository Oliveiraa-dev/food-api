from sqlalchemy import Column, Integer, String, Float
from database import Base # iomport das variavel base que foi criada no arquivo database.py

class ProdutoDB(Base): 
    

    __tablename__ = "produtos" # nome da tabela que vai ser criada no banco de dados.


    
    
    id = Column(Integer, primary_key=True, index=True) # Coluna 'id': É um número inteiro (Integer), é a chave principal (primary_key), 
                                                       # e vai criar números automáticos(index=True)
    
   
    nome = Column(String, index=True)  # Coluna 'nome': É um texto (String)
    
   
    preco = Column(Float)  # Coluna 'preco': É um número decimal (Float)

    