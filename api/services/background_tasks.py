''' This module contains background tasks for collecting container stats '''
import asyncio
from datetime import datetime
import logging
from sqlalchemy.orm import Session
from api.db.database import SessionLocal
from api.services.crane_service import stats
from api.db.crud.app_crud import get_all, get_all_by_service
import api.db.crud.container_stats_crud as ContainerStatsCrud


logger = logging.getLogger(__name__)


class StatsCollector:
    ''' Collects container stats at regular intervals '''
    
    def __init__(self, interval_seconds: int = 60):
        self.interval = interval_seconds
        self.running = False
        self.task = None
    
    async def start(self):
        ''' Start the stats collector background task '''
        if self.running:
            logger.warning("Stats collector is already running")
            return
        
        self.running = True
        self.task = asyncio.create_task(self._collect_loop())
        logger.info(f"Stats collector started with {self.interval}s interval")
    
    async def stop(self):
        ''' Stop the stats collector background task '''
        if not self.running:
            logger.warning("Stats collector is not running")
            return
        
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        logger.info("Stats collector stopped")
    
    async def _collect_loop(self):
        ''' Main collection loop '''
        while self.running:
            try:
                await self._collect_stats()
            except Exception as e:
                logger.error(f"Error collecting stats: {e}")
            
            try:
                await asyncio.sleep(self.interval)
            except asyncio.CancelledError:
                break
    
    async def _collect_stats(self):
        ''' Collect stats for all apps '''
        db: Session = SessionLocal()
        try:
            # Get all active apps (limit high enough to get all)
            apps = get_all_by_service(db, skip=0, limit=10000)
            app_ids = [(app.id, app.user_id) for app in apps if app.deleted_at is None]
            db.close()  # Close session after loading app list
            
            # Collect stats for each app in a separate session
            for app_id, user_id in app_ids:
                # Separate session for stats retrieval
                retrieval_db: Session = SessionLocal()
                app_stats = None
                try:
                    # Get stats from Docker
                    app_stats = await stats(retrieval_db, app_id, user_id)
                    print(f"Collected stats for app {app_id}: {len(app_stats)} containers")
                
                except Exception as e:
                    logger.warning(f"Failed to retrieve stats for app {app_id}: {e}")
                
                finally:
                    # Close retrieval session without committing to avoid persisting app object changes
                    retrieval_db.expunge_all()
                    retrieval_db.close()
                
                # Only store stats if we successfully retrieved them
                if app_stats:
                    storage_db: Session = SessionLocal()
                    try:
                        # Store each container's stats in dedicated storage session
                        for stat in app_stats:
                            ContainerStatsCrud.create(storage_db, app_id, stat)
                        
                        logger.debug(f"Stored stats for app {app_id}: {len(app_stats)} containers")
                    
                    except Exception as e:
                        logger.warning(f"Failed to store stats for app {app_id}: {e}")
                        storage_db.rollback()
                    
                    finally:
                        storage_db.close()
        
        except Exception as e:
            logger.error(f"Error collecting apps list: {e}")
            db.rollback()
        finally:
            if db:
                db.close()


# Global stats collector instance
stats_collector = StatsCollector(interval_seconds=60)


async def start_stats_collection():
    ''' Start the stats collection background task '''
    await stats_collector.start()


async def stop_stats_collection():
    ''' Stop the stats collection background task '''
    await stats_collector.stop()
