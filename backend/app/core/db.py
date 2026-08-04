import ssl

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from app.core.config import settings


class Base(DeclarativeBase):
    pass


def build_pooler_ssl_context() -> ssl.SSLContext:
    # The connection is always TLS-encrypted (verified via a raw handshake:
    # TLSv1.3 / TLS_AES_256_GCM_SHA384). Chain verification is disabled
    # because Supabase's pooler certificate chain doesn't resolve to a root
    # in the system/certifi trust store from this network — confirmed by
    # testing against an up-to-date certifi bundle, not just the OS store.
    # Follow-up: import Supabase's own CA bundle (Project Settings > Database
    # > SSL Configuration) and pass it as `cafile=` here to restore full
    # verify-full chain validation instead of CERT_NONE.
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    return context


# Runtime connects through Supabase's Transaction Pooler (pgbouncer, port 6543),
# which multiplexes connections across transactions and does its own pooling.
# NullPool avoids double-pooling on top of pgbouncer, and disabling asyncpg's
# statement cache avoids "prepared statement does not exist" errors when a
# pooled connection is reused by a different session mid-cache.
engine = create_async_engine(
    settings.database_url,
    poolclass=NullPool,
    connect_args={
        "ssl": build_pooler_ssl_context(),
        "statement_cache_size": 0,
        "prepared_statement_cache_size": 0,
        # Without this, a stalled query (network blip, lock wait) hangs the
        # request indefinitely — no default timeout is set server-side.
        "command_timeout": 30,
    },
)

AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)
