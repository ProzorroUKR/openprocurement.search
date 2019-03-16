# -*- coding: utf-8 -*-

import os
import sys
import fcntl
import signal
import logging
import logging.config

from ConfigParser import ConfigParser

from openprocurement.search.version import __version__
from openprocurement.search.engine import IndexEngine, logger
from openprocurement.search.utils import decode_bool_values, chage_process_user_group

from openprocurement.search.source.orgs import OrgsSource
from openprocurement.search.index.orgs import OrgsIndex

from openprocurement.search.source.tender import TenderSource
from openprocurement.search.index.tender import TenderIndex

from openprocurement.search.source.ocds import OcdsSource
from openprocurement.search.index.ocds import OcdsIndex

from openprocurement.search.source.plan import PlanSource
from openprocurement.search.index.plan import PlanIndex

from openprocurement.search.source.auction import AuctionSource, AuctionSource2
from openprocurement.search.index.auction import AuctionIndex, AuctionIndex2

from openprocurement.search.source.asset import AssetSource
from openprocurement.search.index.asset import AssetIndex

from openprocurement.search.source.dgf_lot import DgfLotSource
from openprocurement.search.index.dgf_lot import DgfLotIndex


engine = type('engine', (), {})()


def sigterm_handler(signo, frame):
    logger.info("Signal received %d", signo)
    if engine and hasattr(engine, 'stop_childs'):
        engine.should_exit = True
        engine.stop_childs()
    signal.alarm(3)
    # sys.exit(0)


def main():
    if len(sys.argv) < 2:
        print("Usage: index_worker etc/search.ini [custom_index_names_file]")
        sys.exit(1)

    if '--version' in sys.argv:
        print(__version__)
        sys.exit(0)

    parser = ConfigParser()
    parser.read(sys.argv[1])
    config = dict(parser.items('search_engine'))
    config = decode_bool_values(config)

    # disable slave mode if used custom_index_names
    if len(sys.argv) > 2:
        config['index_names'] = sys.argv[2]
        config['slave_mode'] = ''
        config['start_wait'] = 0

    logging.config.fileConfig(sys.argv[1])

    logger.info("Starting ProZorro openprocurement.search.index_worker v%s", __version__)
    logger.info("Copyright (c) 2015-2018 Volodymyr Flonts <flyonts@gmail.com>")

    try:
        chage_process_user_group(config, logger)
    except Exception as e:
        logger.error("Can't change process user: %s", str(e))

    # try get exclusive lock to prevent second start
    lock_filename = config.get('pidfile', '')
    if not lock_filename:
        lock_filename = config.get('index_names', 'index_worker') + '.lock'
    lock_file = open(lock_filename, "w")
    try:
        fcntl.lockf(lock_file, fcntl.LOCK_EX + fcntl.LOCK_NB)
        lock_file.write(str(os.getpid()) + "\n")
        lock_file.flush()
    except:
        logger.error("Can't get lock %s maybe already started",
            lock_filename)
        lock_file.close()
        return 1

    signal.signal(signal.SIGTERM, sigterm_handler)
    # signal.signal(signal.SIGINT, sigterm_handler)

    try:
        global engine
        engine = IndexEngine(config)
        if config.get('orgs_db', None):
            source = OrgsSource(config, True)
            OrgsIndex(engine, source, config)
        if config.get('tender_api_url', None):
            source = TenderSource(config, True)
            TenderIndex(engine, source, config)
        if config.get('ocds_dir', None):
            source = OcdsSource(config)
            OcdsIndex(engine, source, config)
        if config.get('plan_api_url', None):
            source = PlanSource(config, True)
            PlanIndex(engine, source, config)
        if config.get('auction_api_url', None):
            source = AuctionSource(config, True)
            AuctionIndex(engine, source, config)
        if config.get('auction2_api_url', None):
            source = AuctionSource2(config, True)
            AuctionIndex2(engine, source, config)
        if config.get('asset_api_url', None):
            source = AssetSource(config, True)
            AssetIndex(engine, source, config)
        if config.get('lot_api_url', None):
            source = DgfLotSource(config, True)
            DgfLotIndex(engine, source, config)
        engine.run()
    except Exception as e:
        logger.exception("Unhandled Exception: %s", str(e))
    finally:
        lock_file.close()
        os.remove(lock_filename)
        if engine and hasattr(engine, 'stop_childs'):
            engine.stop_childs()
        logger.info("Shutdown")

    return 0


if __name__ == "__main__":
    main()
