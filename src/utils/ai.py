import asyncio
import json
import logging
from pprint import pprint
import aiohttp

from config import IOINTELLIGENCE_API_KEY

logger = logging.getLogger(__name__)

# from requests import Session

model = {"main": "openai/gpt-oss-120b", "black_list":[]}
cool_models = ['deepseek-ai', 'openai', 'Qwen'] #полная хуйня 

cool_models_list = ["openai/gpt-oss-120b", "mistralai/Mistral-Large-Instruct-2411", "Qwen/Qwen3-235B-A22B-Thinking-2507", "openai/gpt-oss-20b", "deepseek-ai/DeepSeek-R1-0528", ]
                    
fast = ["openai/gpt-oss-120b", "mistralai/Mistral-Large-Instruct-2411"]
                    

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {IOINTELLIGENCE_API_KEY}",
}


async def get_models():

    url = "https://api.intelligence.io.solutions/api/v1/models"
    data = await call_neural_api_get(url)

    models_list = []

    for i in range(len(data["data"])):
        models_list.append(data["data"][i]["id"])

    logger.debug(f"список моделей: {models_list}")
    return models_list


async def check_best_model(best_model):
    model["main"] = best_model
    status, response_json = await get_ai_response('hi')
    return status != 429
    # if status == 429:
    

async def get_best_model():

    models = await get_models()
    # all_models = list(models)


    
    for i in cool_models_list:
        if i in models:
            if await check_best_model(i):
                return i
            # all_models.remove(i)
            

    else:
        logger.warning("нет качественной бесплатной нейросети")

        for i in models:
            if await check_best_model(i):
                return i
        else:
            logger.error("нет бесплатной нейросети")


    # for i in models:
        
    #     for cool_model in cool_models:
    #         if cool_model in i:
    #             if await check_best_model(i):
    #                 return i
    #             bad_models.remove(i)

    # else:
    #     logger.warning("нет качественной бесплатной нейросети")

    #     for i in bad_models:
    #         if await check_best_model(i):
    #             return i
    #     else:
    #         logger.error("нет бесплатной нейросети")


    # return model


async def call_neural_api(url, data):
    async with aiohttp.ClientSession() as session:
        async with session.post(
            url, headers=headers, json=data, timeout=500  # Таймаут в секундах
        ) as response:
            try:
                return (response.status, await response.json())
            except aiohttp.client_exceptions.ContentTypeError:
                print(response.text())
                return (response.status, response.text())



async def call_neural_api_get(url):
    connector = aiohttp.TCPConnector(ssl=False)
    async with aiohttp.ClientSession(connector=connector) as session:
        async with session.get(
            url, headers=headers, timeout=500  # Таймаут в секундах
        ) as response:
            response.raise_for_status()
            return await response.json()


async def get_ai_response(text):
        data = {
            "model": f"{model['main']}",
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": f"{text}"},
            ],
        }
        return await call_neural_api(
            "https://api.intelligence.io.solutions/api/v1/chat/completions", data
        )

async def get_answer(text):
    status, response_json = await get_ai_response(text)

    if status in [400, 429]:
        logger.info("смена модели")
        model["main"] = await get_best_model()
        logger.info(f'модель: {model["main"]}')

        status, response_json = await get_ai_response(text)

    if status == 503:
        logger.warning("ошибка 503 io.net Internal Server Error")
        for _ in range(4):
            await asyncio.sleep(1)
            status, response_json = await get_ai_response(text)

            if status in [400, 429]:
                logger.info("смена модели")
                model["main"] = await get_best_model()
                logger.info(f'модель: {model["main"]}')

                status, response_json = await get_ai_response(text)
                # status, response_json = await get_ai_response(text)
            if status != 503:
                break





    logging.debug(f'choices {status}, {response_json}')


    answer_obj = response_json["choices"][0]["message"]["reasoning_content"]
    logger.debug(f"рассуждение: {answer_obj}")


    answer_obj = response_json["choices"][0]["message"]["content"].split('</think>')[-1]
    logger.debug(f"ответ: {answer_obj}")




    tk_count = response_json["usage"]["total_tokens"]

    data = {
        "answer": answer_obj,
        "tk_count": tk_count,
    }

    return data
