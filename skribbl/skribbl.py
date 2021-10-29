import attr
import logging

from functools import wraps
from socketio import AsyncClient
from typing import Callable, NamedTuple, Type, Optional, TypedDict, Any, Union

from contextlib import AbstractAsyncContextManager, asynccontextmanager

from .errors import LoginError
from .models import Avatar, Language, Player

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


class Entry(NamedTuple):
    player: Player
    score: int
    guessed_word: bool 


@attr.s(slots=True)
class Game:
    """ Game state """
    bot_id: int = attr.ib()
    owner_id: int = attr.ib()
    language: Language = attr.ib(converter=Language)
    canvas: list = attr.ib(factory=list)
    current_word: Optional[str] = attr.ib(default=None)
    players: dict[int, Entry] = attr.ib(factory=dict)

    def owner(self) -> Optional[Entry]:
        """ Returns owner entry. None if in a public game """
        return self.players.get(self.owner_id)

    def me(self) -> Entry:
        """ Returns current player entry """
        return self.players[self.bot_id]


LOGIN_URL: str = "wss://skribbl.io:4999"


class Login(NamedTuple):
    """ Login response """
    code: int = 0
    host: Optional[str] = None


class UserProfile(TypedDict):
    code: str
    join: str
    language: str
    createPrivate: bool
    name: str
    avatar: Union[list[int], tuple[int, int, int, int]]


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
        avatar=attr.astuple(profile.avatar),
    )

    async with client_manager(**kwargs) as socket:
        await socket.connect(LOGIN_URL, transports="websocket")
        await socket.emit("login", profile)

        @socket.event
        def result(r: dict) -> None:
            nonlocal login
            login = Login(**r)

    if not login.code:
        raise LoginError("Server returned bad code")

    return login.host, profile


class Skribbl(AbstractAsyncContextManager):
    __slots__ = 'game', '_socket'

    def __init__(self, socket: Optional[AsyncClient] = None, **kwargs):
        self._socket = socket or make_client(**kwargs)

        # Setup event handlers
        self.socket.on("chat", self.on_chat)
        self.socket.on("lobbyConnected", self.on_lobby_connected)
        self.socket.on("lobbyCurrentWord", self.on_lobby_current_word)
        self.socket.on("lobbyLanguage", self.on_lobby_set_language)
        self.socket.on("lobbyPlayerDisconnected", self.on_lobby_player_disconnect)
        self.socket.on("lobbyPlayerConnected", self.on_lobby_player_join)

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
        def all(name, *data) -> None:
            print(name, data)

        await socket.connect(host, transports="websocket")
        await socket.emit("userData", profile)

        return cls(socket)

    def json_parse(fn: Callable[..., Any]):
        @wraps(fn)
        def wrapper(self: 'Skribbl', data: dict, *args, **kwargs) -> Any:
            return fn(self, *args, **data, **kwargs)
        return wrapper

    @json_parse
    def on_chat(self, id: int, message: str) -> None:
        player = self.game.players.get(id, id)
        print(f"Chat: {player}, {message}")

    def on_lobby_player_disconnect(self, id: int) -> None:
        player = self.game.players.pop(id, id)
        print(f"Player disconnected: {player}")

    def on_lobby_current_word(self, word: str) -> None:
        print(f"Current word: {word}")
        self.game.current_word = word

    @json_parse
    def on_lobby_connected(self, language: str, drawCommands: list[list], players: list[dict], ownerID: int, myID: int, **_) -> None:
        print(f"Connected to lobby")
        self.game = Game(myID, ownerID, language.capitalize())
        for player in players:
            self.on_lobby_player_join(player)

    @json_parse
    def on_lobby_player_join(self, id: int, name: str, avatar: list[int], score: int, guessedWord: bool) -> None:
        player = Player(name, Avatar(*avatar))
        print(f"Player joined: {player}")
        self.game.players[id] = Entry(player, score=score, guessed_word=guessedWord)

    def on_lobby_set_language(self, language: str) -> None:
        print(f"Language set: {language}")
        self.game.language = Language(language.capitalize())

    @property
    def socket(self) -> AsyncClient:
        return self._socket

    async def wait(self) -> None:
        await self.socket.wait()

    def __repr__(self) -> str:
        return f"{self.game!r}"

    def __str__(self) -> str:
        return f"{self.game!s}"

    async def __aexit__(self, *_) -> None:
        await self.wait()
