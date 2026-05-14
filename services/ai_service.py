from groq import AsyncGroq
from core.config import settings
from database.unit_of_work import UnitOfWork
from core.exceptions import (
ClientNotFoundError
)


groq_client = AsyncGroq(api_key=settings.GROQ_API_KEY)

class AiService:

    @staticmethod
    async def get_recomendations(products: list[str]) -> str:
        products_str = ", ".join(products)
        prompt = f"Customer bought: {products_str}. Recommend 3 similar products, Be brief."
        response = await groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content

    @staticmethod
    async def get_client_recommendations(client_id: int) -> str:
        async with UnitOfWork() as uow:
            client = await uow.client.client_with_orders(client_id)
            if not client:
                raise ClientNotFoundError(client_id)
            products = [
                op.product.name
                for order in client.orders
                for op in order.order_products
            ]
            if not products:
                return "No purchase history found. Buy something first to get personalized recommendations."
            return await AiService.get_recomendations(products)
            
    @staticmethod
    async def generate_product_description(product_name: str) -> str:
        prompt = f"Write a short product description for an online store for: {product_name}. 2-3 sentences, be concise and appealing."
        response = await groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content

    @staticmethod
    async def chat(message: str) -> str:
        response = await groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a helpful assistant for an online store..."},
                {"role": "user", "content": message}
            ]
        )
        return response.choices[0].message.content
    
    @staticmethod
    async def search_products(query: str, products: list[str]) -> str:
        products_str = ", ".join(products)
        prompt = f"From this product list: {products_str}. Return only the names that match this query: '{query}'. Return as comma-separated list, nothing else."
        response = await groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    
    @staticmethod
    async def ai_search(query: str):
        async with UnitOfWork() as uow:
            products = await uow.product.get_products(limit=100, offset=0)
            if not products:
                return "No products available"
            products_name = [p.name for p in products]
        return await AiService.search_products(query, products_name)





