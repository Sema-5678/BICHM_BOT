import socket
import struct
import time
from typing import Optional, Dict, List

class RCONClient:
    def __init__(self, host: str, port: int, password: str, timeout: float = 5.0):
        self.host = host
        self.port = port
        self.password = password
        self.timeout = timeout
        self.socket = None

    def connect(self) -> bool:
        """Establish RCON connection with proper error handling"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(self.timeout)
            self.socket.connect((self.host, self.port))
            
            # Authentication
            auth_packet = self._build_packet(3, self.password)
            self.socket.send(auth_packet)
            
            # Wait for auth response
            time.sleep(0.1)
            response = self._read_packet()
            return response.get('id') != -1
            
        except socket.timeout:
            print(f"Timeout connecting to {self.host}:{self.port}")
            return False
        except Exception as e:
            print(f"Connection error: {e}")
            return False

    def transfer_items(self, player: str, items: List[Dict]) -> bool:
        """Transfer items with enhanced error handling"""
        if not self.socket:
            if not self.connect():
                return False

        try:
            # Check if player is online
            if not self._is_player_online(player):
                print(f"Player {player} is offline")
                return False
                
            # Send items
            for item in items:
                command = f"give {player} {item['id']} {item['count']}"
                if not self._send_command(command):
                    return False
                    
            return True
            
        except Exception as e:
            print(f"Transfer error: {e}")
            return False

    def _is_player_online(self, player: str) -> bool:
        """Check if player is online"""
        response = self._send_command("list")
        return player.lower() in response.lower() if response else False

    def _send_command(self, command: str) -> Optional[str]:
        """Send RCON command and get response"""
        packet = self._build_packet(2, command)
        self.socket.send(packet)
        response = self._read_packet()
        return response.get('payload') if response else None

    def _build_packet(self, packet_type: int, payload: str) -> bytes:
        """Build RCON packet"""
        packet_id = 1
        data = struct.pack('<iii', 
            len(payload) + 10, 
            packet_id, 
            packet_type) + payload.encode('utf-8') + b'\x00\x00'
        return data

    def _read_packet(self) -> Optional[Dict]:
        """Read RCON packet with robust error handling"""
        try:
            # Read packet size (4 bytes)
            size_data = self._receive_data(4)
            if not size_data or len(size_data) != 4:
                return None
                
            size = struct.unpack('<i', size_data)[0]
            if size <= 0:
                return None
                
            # Read full packet
            packet_data = self._receive_data(size)
            if not packet_data or len(packet_data) < 8:
                return None
                
            packet_id, packet_type = struct.unpack('<ii', packet_data[:8])
            payload = packet_data[8:-2].decode('utf-8')
            
            return {'id': packet_id, 'type': packet_type, 'payload': payload}
            
        except Exception as e:
            print(f"Packet read error: {e}")
            return None

    def _receive_data(self, size: int) -> Optional[bytes]:
        """Reliably receive data with timeout"""
        data = b''
        start_time = time.time()
        
        while len(data) < size:
            if time.time() - start_time > self.timeout:
                raise socket.timeout("Receive timeout")
                
            try:
                chunk = self.socket.recv(size - len(data))
                if not chunk:
                    break
                data += chunk
            except socket.timeout:
                continue
                
        return data if len(data) == size else None

    def close(self):
        """Close connection safely"""
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            finally:
                self.socket = None


# def transfer_items_to_player(player_name: str, items: List[Dict], rcon_config: Dict):
#     """Example usage: Transfer items to player by their user ID"""
#     # In a real implementation, you would get player_name from your database
#     # player_name = f"Player_{user_id}"  # Replace with actual lookup
    
#     rcon = RCONClient(
#         host=rcon_config['host'],
#         port=rcon_config['port'],
#         password=rcon_config['password']
#     )
    
#     try:
#         if not rcon.connect():
#             return False
            
#         # First check if player is online
#         if not rcon._is_player_online(player_name):
#             print(f"Player {player_name} is offline")
#             return False
            
#         # Transfer items if player is online
#         return rcon.transfer_items(player_name, items)
        
#     except Exception as e:
#         print(f"Error transferring items: {e}")
#         return False
#     finally:
#         rcon.close()




# def transfer_items_to_player(player_name: str, items: list, rcon_config: dict):
#     """Улучшенная версия с обработкой ошибок"""
#     rcon = RCONClient(
#         host=rcon_config['host'],
#         port=rcon_config['port'],
#         password=rcon_config['password'],
#         timeout=5.0
#     )
    
#     try:
#         if not rcon.connect():
#             print("Ошибка подключения к RCON")
#             return False

#         # Проверка онлайн-статуса
#         online = rcon._send_command("list")
#         if not online or player_name not in online:
#             print(f"Игрок {player_name} оффлайн или не найден")
#             return False

#         # Передача предметов
#         for item in items:
#             cmd = f"give {player_name} {item['id']} {item['count']}"
#             if not rcon._send_command(cmd):
#                 print(f"Ошибка передачи предмета: {item['id']}")
#                 return False
                
#         return True
        
#     except Exception as e:
#         print(f"Критическая ошибка: {str(e)}")
#         return False
#     finally:
#         rcon.close()





def transfer_items_to_player(player_name: str, items: list, rcon_config: dict):
    """Улучшенная версия с полной обработкой ошибок для модов"""
    rcon = RCONClient(
        host=rcon_config['host'],
        port=rcon_config['port'],
        password=rcon_config['password'],
        timeout=15.0  # Увеличенный таймаут для модов
    )
    
    try:
        # Подключение с 3 попытками
        for attempt in range(3):
            try:
                if not rcon.connect():
                    print(f"Попытка {attempt+1}: Ошибка подключения RCON")
                    time.sleep(3)
                    continue
                
                # Улучшенная проверка игрока (для модов)
                online = rcon._send_command("list")
                if not online:
                    print("Сервер не вернул список игроков")
                    return False
                
                # Игрок считается онлайн если есть ANY совпадение в ответе
                if not any(player_name.lower() in line.lower() for line in online.split('\n')):
                    print(f"Игрок {player_name} оффлайн. Полный ответ сервера: {online}")
                    return False
                
                # Передача предметов с проверкой
                for item in items:
                    cmd = f"give {player_name} {item['id']} {item['count']}"
                    result = rcon._send_command(cmd)
                    
                    if not result or any(err in result.lower() for err in ["error", "не найден", "не существует"]):
                        print(f"Ошибка выдачи предмета {item['id']}: {result}")
                        return False
                        
                return True
                
            except socket.timeout:
                print(f"Попытка {attempt+1}: Таймаут операции")
                continue
            except Exception as e:
                print(f"Попытка {attempt+1}: {type(e).__name__}: {str(e)}")
                continue
                
        return False
        
    except Exception as e:
        print(f"Критическая ошибка: {type(e).__name__}: {str(e)}")
        return False
    finally:
        rcon._safe_close()

        
# Example config (put your actual RCON details here)
RCON_CONFIG = {
    # 'host': '185.9.145.7:42103',
    'host': '185.9.145.7',

    'port': 25575,
    # 'port': 42103,

    'password': 'asr-d5211'
}

# Example usage:
items = [{'id': 'stone', 'count': 5}]
transfer_items_to_player("TmuR789", items, RCON_CONFIG)





import socket
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(3)
    s.connect(('185.9.145.7', 42103))
    print("Порт доступен!")
    s.close()
except Exception as e:
    print(f"Ошибка: {e}")