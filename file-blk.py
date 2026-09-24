from .web.gmail import GmailPlugin
from .web.outlook import OutlookPlugin
from .web.facebook import FacebookPlugin
from .web.instagram import InstagramPlugin
from .web.twitter import TwitterPlugin
from .web.linkedin import LinkedInPlugin
from .web.tiktok import TikTokPlugin
from .web.reddit import RedditPlugin
from .web.discord import DiscordPlugin
from .web.yahoo import YahooPlugin
from .web.protonmail import ProtonMailPlugin
from .web.icloud import iCloudPlugin
from .web.amazon import AmazonPlugin
from .web.netflix import NetflixPlugin
from .web.spotify import SpotifyPlugin
from .web.github import GitHubPlugin

from .protocol.ssh import SSHPlugin
from .protocol.mysql import MySQLPlugin
from .protocol.ftp import FTPPlugin
from .protocol.postgres import PostgreSQLPlugin
from .protocol.smtp import SMTPPlugin

PLUGINS = [
    GmailPlugin,
    OutlookPlugin,
    FacebookPlugin,
    InstagramPlugin,
    TwitterPlugin,
    LinkedInPlugin,
    TikTokPlugin,
    RedditPlugin,
    DiscordPlugin,
    YahooPlugin,
    ProtonMailPlugin,
    iCloudPlugin,
    AmazonPlugin,
    NetflixPlugin,
    SpotifyPlugin,
    GitHubPlugin,
    SSHPlugin,
    MySQLPlugin,
    FTPPlugin,
    PostgreSQLPlugin,
    SMTPPlugin,
]