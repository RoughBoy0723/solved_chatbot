import discord
import requests
import logging
import json
import os

intents = discord.Intents.default()
intents.message_content = True  # Message Content Intent를 활성화합니다.
client = discord.Client(intents=intents)

FILE_PATH = r'유저 데이터 저장 폴더 PATH'
DISCORD_BOT_TOKEN = '디스코드 챗 봇 토큰'
SOLVED_AC_API_URL = 'https://solved.ac/api/v3'

@client.event
async def on_ready():
    logging.info(f'Logged in as {client.user}')
    print(f'We have logged in as {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    logging.info(f'Received message: {message.content} from {message.author}')
    
    if message.content.startswith("!n "):
        boj_id = message.content.split("!n ")[1].strip()
        logging.info(f'Processing request for BOJ ID: {boj_id}')
        
        problems_solved, current_rating = get_boj_info(boj_id)
        
        response_text = (f"백준 ID {boj_id}의 통계입니다:\n"
                         f"총 풀린 문제 수: {problems_solved}\n"
                         f"현재 레이팅: {current_rating}")
        
        await message.channel.send(response_text)
        
        logging.info(f'Sent response: {response_text}')
    
    if message.content.startswith("!r "):
        boj_id = message.content.split("!r ")[1].strip()
        logging.info(f'Registering request for BOJ ID: {boj_id}')
        
        if is_boj_info_file_exist(boj_id):
            response_text = f"백준 ID {boj_id}는 이미 등록되었습니다."
            logging.info(f'{boj_id} already registered')
        else:
            problems_solved, current_rating = get_boj_info(boj_id)
            save_boj_info_to_file(boj_id, problems_solved, current_rating)
            response_text = (f"백준 ID {boj_id}의 통계가 파일에 저장되었습니다.\n"
                             f"총 풀린 문제 수: {problems_solved}\n"
                             f"현재 레이팅: {current_rating}")
            logging.info(f'Saved info for BOJ ID: {boj_id} to file')
        
        await message.channel.send(response_text)
    
    if message.content.startswith("!update"):
        logging.info('Updating all registered BOJ IDs')
        
        updated_info = update_all_boj_info()
        
        response_text = "모든 등록된 백준 ID의 통계가 업데이트되었습니다:\n"
        for boj_id, info in updated_info.items():
            response_text += (f"{boj_id}:\n"
                              f"총 풀린 문제 수: {info['solvedCount']}\n"
                              f"현재 레이팅: {info['rating']}\n\n")
        
        await message.channel.send(response_text)
        
        logging.info('Updated all registered BOJ IDs')
    
    if message.content.startswith("!c "):
        boj_id = message.content.split("!c ")[1].strip()
        logging.info(f'Comparing current stats for BOJ ID: {boj_id}')
        
        if not is_boj_info_file_exist(boj_id):
            response_text = f"백준 ID {boj_id}는 등록되어 있지 않습니다. 먼저 !r 명령어로 등록해 주세요."
            logging.info(f'{boj_id} is not registered')
        else:
            current_problems_solved, current_rating = get_boj_info(boj_id)
            registered_info = load_boj_info_from_file(boj_id)
            if registered_info:
                registered_problems_solved = registered_info['solvedCount']
                registered_rating = registered_info['rating']
                
                problems_solved_diff = current_problems_solved - registered_problems_solved
                rating_diff = current_rating - registered_rating
                rating_diff_per = round(((current_rating - registered_rating) / registered_rating) * 100, 2)
                
                response_text = (f"백준 ID {boj_id}의 현재 통계입니다:\n"
                                 f"총 풀린 문제 수: {current_problems_solved}\n"
                                 f"현재 레이팅: {current_rating}\n\n"
                                 f"일요일 이후 증가량:\n"
                                 f"풀린 문제 수: {problems_solved_diff}\n"
                                 f"레이팅 증가량: {rating_diff}, {rating_diff_per}%")
                logging.info(f'Compared info for BOJ ID: {boj_id}')
            else:
                response_text = f"백준 ID {boj_id}의 등록된 정보를 불러오는 데 실패했습니다."
                logging.error(f'Failed to load registered info for {boj_id}')
        
        await message.channel.send(response_text)

def get_boj_info(boj_id):
    problems_solved = get_boj_problems_solved(boj_id)
    current_rating = get_solved_ac_rating(boj_id)
    return problems_solved, current_rating

def get_boj_problems_solved(boj_id):
    url = f"{SOLVED_AC_API_URL}/user/show?handle={boj_id}"
    response = requests.get(url)
    logging.info(f"API Response for user/show: {response.text}")  # 디버깅 로그 추가
    if response.status_code == 200:
        data = response.json()
        total_solved = data.get('solvedCount', 0)
        logging.info(f'{boj_id} has solved {total_solved} problems')
        return total_solved
    logging.error(f'Failed to get problem stats for {boj_id}')
    return 0

def get_solved_ac_rating(boj_id):
    url = f"{SOLVED_AC_API_URL}/user/show?handle={boj_id}"
    response = requests.get(url)
    logging.info(f"API Response for user/show: {response.text}")  # 디버깅 로그 추가
    if response.status_code == 200:
        data = response.json()
        current_rating = data.get('rating', 0)
        logging.info(f'{boj_id} current rating is {current_rating}')
        return current_rating
    logging.error(f'Failed to get rating for {boj_id}')
    return 0

def save_boj_info_to_file(boj_id, problems_solved, current_rating):
    filename = f"{FILE_PATH}{boj_id}_info.json"
    data = {
        'boj_id': boj_id,
        'solvedCount': problems_solved,
        'rating': current_rating
    }
    with open(filename, 'w') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)
    logging.info(f'Saved info for {boj_id} to {filename}')

def is_boj_info_file_exist(boj_id):
    filename = f"{FILE_PATH}{boj_id}_info.json"
    return os.path.exists(filename)

def load_boj_info_from_file(boj_id):
    filename = f"{FILE_PATH}{boj_id}_info.json"
    if not os.path.exists(filename):
        logging.error(f'File {filename} does not exist')
        return None
    with open(filename, 'r') as file:
        data = json.load(file)
    logging.info(f'Loaded info for {boj_id} from {filename}')
    return data

def update_all_boj_info():
    updated_info = {}
    for filename in os.listdir(FILE_PATH):
        if filename.endswith("_info.json"):
            boj_id = filename.split("_info.json")[0]
            problems_solved, current_rating = get_boj_info(boj_id)
            save_boj_info_to_file(boj_id, problems_solved, current_rating)
            updated_info[boj_id] = {
                'solvedCount': problems_solved,
                'rating': current_rating
            }
    return updated_info

client.run(DISCORD_BOT_TOKEN)