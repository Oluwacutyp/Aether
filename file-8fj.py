"""
Aether Plugins
Complete plugin set.
"""

from .web.gmail import GmailPlugin
from .web.outlook import OutlookPlugin
from .web.facebook import FacebookPlugin
from .web.instagram import InstagramPlugin
from .web.twitter import TwitterPlugin
from .web.linkedin import LinkedInPlugin
from .web.tiktok import TikTokPlugin
from .web.reddit import RedditPlugin
from .web.discord import DiscordPlugin
from .web.telegram import TelegramPlugin
from .web.amazon import AmazonPlugin
from .web.yahoo import YahooPlugin
from .web.protonmail import ProtonMailPlugin
from .web.icloud import iCloudPlugin
from .web.zoho import ZohoPlugin
from .web.generic_form import GenericFormPlugin

from .protocol.ssh import SSHPlugin
from .protocol.mysql import MySQLPlugin
from .protocol.ftp import FTPPlugin
from .protocol.smtp import SMTPIMAPPlugin
from .protocol.postgresql import PostgreSQLPlugin
from .protocol.mssql import MSSQLPlugin
from .protocol.redis import RedisPlugin
from .protocol.mongodb import MongoDBPlugin
from .protocol.rdp import RDPPlugin
from .protocol.smb import SMBPlugin
from .protocol.winrm import WinRMPlugin
from .protocol.ldap import LDAPPlugin

PLUGINS = [
    # Web / Social / Email (16 plugins)
    GmailPlugin,
    OutlookPlugin,
    FacebookPlugin,
    InstagramPlugin,
    TwitterPlugin,
    LinkedInPlugin,
    TikTokPlugin,
    RedditPlugin,
    DiscordPlugin,
    TelegramPlugin,
    AmazonPlugin,
    YahooPlugin,
    ProtonMailPlugin,
    iCloudPlugin,
    ZohoPlugin,
    GenericFormPlugin,
    
    # Protocols (12 plugins)
    SSHPlugin,
    MySQLPlugin,
    FTPPlugin,
    SMTPIMAPPlugin,
    PostgreSQLPlugin,
    MSSQLPlugin,
    RedisPlugin,
    MongoDBPlugin,
    RDPPlugin,
    SMBPlugin,
    WinRMPlugin,
    LDAPPlugin,
]