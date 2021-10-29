from functools import wraps
import logging

from socketio import AsyncClient
from typing import Awaitable, Callable, Type, Optional, Dict, NamedTuple, Any

from dataclasses import dataclass, field
from contextlib import AbstractAsyncContextManager, asynccontextmanager

from .errors import LoginError
from .models import Avatar, Language, Player, UserProfile

log = logging.getLogger("skribbl")

def make_client(**kwargs) -> AsyncClient:
    s = AsyncClient(**kwargs)
    s.event(s.disconnect)
    return s


@asynccontextmanager
async def client_manager(**kwargs) -> AsyncClient:
    s = make_client(**kwargs)
    try:
        yield s
    finally:
        await s.wait()


class ListEntry(NamedTuple):
    player: Player
    score: int


@dataclass
class Game:
    """ Game state """
    canvas = 0
    current_word: Optional[str] = None
    language: Language = Language.English
    players: dict[int, ListEntry] = field(default_factory=dict)


LOGIN_URL: str = "wss://skribbl.io:4999"


class Login(NamedTuple):
    """ Login response """
    code: int = 0
    host: Optional[str] = None


async def login(
    profile: Player,
    key: str = '',
    code: str = '',
    language: Language = Language.English,
    **kwargs
) -> tuple[str, UserProfile]:
    """ Send login request to server and returns host and user profile """
    login = Login()

    profile = UserProfile(
        code=key,
        join=code,
        name=profile.name,
        createPrivate=False,
        language=language.value,
        avatar=profile.avatar,
    )

    async with client_manager(**kwargs) as socket:
        await socket.connect(LOGIN_URL, transports="websocket")
        await socket.emit("login", profile)

        @socket.event
        async def result(r: dict) -> None:
            nonlocal login
            login = Login(**r)

    if not login.code:
        raise LoginError("Server returned bad code")

    return login.host, profile


class Skribbl(AbstractAsyncContextManager):
    __slots__ = 'game', '_socket'

    def __init__(self, socket: Optional[AsyncClient] = None, **kwargs):
        self.game = Game()
        self._socket = socket or make_client(**kwargs)

        # Setup event handlers
        self.socket.on("chat", self.on_chat)
        self.socket.on("lobbyConnected", self.on_lobby_connected)
        self.socket.on("lobbyCurrentWord", self.on_lobby_current_word)
        self.socket.on("lobbyLanguage", self.on_lobby_set_language)
        # self.socket.on("lobbyPlayerConnected", self.on_lobby_player_join)

    @classmethod
    async def join(
        cls: Type['Skribbl'],
        profile: Player,
        key: str = '',
        code: str = '',
        language: Language = Language.English,
        **kwargs
    ) -> 'Skribbl':
        """ Code can be left as an empty string to join public game """
        host, profile = await login(profile, key, code, language, **kwargs)
        socket = make_client(**kwargs)

        @socket.on('*')
        async def all(name, *data) -> None:
            print(name, data)

        await socket.connect(host, transports="websocket")
        await socket.emit("userData", profile)

        return cls(socket)

    def json_parse(fn: Callable[..., Awaitable[Any]]):
        @wraps(fn)
        async def wrapper(self: 'Skribbl', data: dict, *args, **kwargs) -> Any:
            return await fn(self, *args, **data, **kwargs)
        return wrapper

    @json_parse
    async def on_chat(self, id: int, message: str) -> None:
        player = self.game.players.get(id, id)
        log.info(f"Chat: {player}, {message}")

    async def on_lobby_current_word(self, word: str) -> None:
        log.info(f"Current word: {word}")
        self.game.current_word = word

    async def on_lobby_connected(self, lobby) -> None:
        log.info(f"Lobby: {lobby}")

    @json_parse
    async def on_lobby_player_join(self, id: int, name: str, avatar: tuple[int, int, int, int], score: int) -> None:
        avatar = Avatar(**avatar)
        log.info(f"Player joined: {name}, {avatar}")
        self.game.players[id] = ListEntry(Player(name, avatar), score)

    async def on_lobby_set_language(self, language: str) -> None:
        log.info(f"Language set: {language}")
        self.game.language = Language(language.capitalize())

    @property
    def socket(self) -> AsyncClient:
        return self._socket

    async def wait(self) -> None:
        await self.socket.wait()

    async def __aexit__(self, *_) -> None:
        await self.wait()