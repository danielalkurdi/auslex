#!/usr/bin/env python3
"""
Corpus Processing Script for AusLex AI System
Processes HuggingFace legal corpus and populates vector database
"""

import os
import sys
import json
import asyncio
import logging
import argparse
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add API directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'api'))

try:
    from corpus_processor import (
        get_corpus_processor,
        process_legal_corpus,
        get_corpus_processing_status
    )
    from vector_search_engine import create_vector_search_config
    CORPUS_PROCESSING_AVAILABLE = True
except ImportError as e:
    logger.error(f"Corpus processing components not available: {e}")
    CORPUS_PROCESSING_AVAILABLE = False

class CorpusProcessingManager:
    """Manages corpus processing operations with CLI interface"""
    
    def __init__(self):
        self.config = None
        self.processor = None
    
    async def initialize(self) -> bool:
        """Initialize corpus processing manager"""
        try:
            if not CORPUS_PROCESSING_AVAILABLE:
                logger.error("Corpus processing components not available")
                return False
            
            # Create configuration
            self.config = create_vector_search_config()
            
            # Get processor
            self.processor = await get_corpus_processor(self.config)
            
            logger.info("Corpus processing manager initialized")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize corpus processing manager: {e}")
            return False
    
    async def process_corpus(self,
                           batch_size: int = 100,
                           start_index: int = 0,
                           max_documents: Optional[int] = None,
                           dataset_name: str = "isaacus/open-australian-legal-corpus",
                           checkpoint_file: Optional[str] = None,
                           save_checkpoints: bool = True) -> Dict[str, Any]:
        """Process legal corpus with options"""
        
        if not self.processor:
            raise RuntimeError("Processor not initialized")
        
        try:
            logger.info("🚀 Starting Legal Corpus Processing")
            logger.info("=" * 60)
            logger.info(f"📊 Configuration:")
            logger.info(f"   - Dataset: {dataset_name}")
            logger.info(f"   - Batch size: {batch_size}")
            logger.info(f"   - Start index: {start_index}")
            logger.info(f"   - Max documents: {max_documents or 'All'}")
            logger.info(f"   - Checkpoints: {'Enabled' if save_checkpoints else 'Disabled'}")
            
            # Load corpus dataset
            success = await self.processor.load_legal_corpus(dataset_name)
            if not success:
                raise RuntimeError("Failed to load legal corpus dataset")
            
            # Process corpus
            if checkpoint_file and os.path.exists(checkpoint_file):
                logger.info(f"📂 Resuming from checkpoint: {checkpoint_file}")
                metrics = await self.processor.resume_processing(checkpoint_file)
            else:
                metrics = await process_legal_corpus(
                    batch_size=batch_size,
                    start_index=start_index,
                    max_documents=max_documents,
                    dataset_name=dataset_name
                )
            
            # Save final checkpoint if requested
            if save_checkpoints:
                checkpoint_path = self._get_checkpoint_path()
                await self.processor.save_checkpoint(
                    checkpoint_path,
                    start_index + metrics.processed_documents
                )
            
            # Generate report
            report = {
                'status': 'completed',
                'metrics': {
                    'total_documents': metrics.total_documents,
                    'processed_documents': metrics.processed_documents,
                    'failed_documents': metrics.failed_documents,
                    'skipped_documents': metrics.skipped_documents,
                    'success_rate': metrics.success_rate,
                    'processing_time': metrics.processing_time,
                    'processing_speed': metrics.processing_speed,
                    'embeddings_generated': metrics.embeddings_generated,
                    'total_tokens': metrics.total_tokens
                },
                'configuration': {
                    'dataset_name': dataset_name,
                    'batch_size': batch_size,
                    'start_index': start_index,
                    'max_documents': max_documents
                },
                'timestamp': datetime.utcnow().isoformat()
            }
            
            logger.info("=" * 60)
            logger.info("✅ Corpus Processing Completed Successfully")
            self._print_processing_summary(report)
            
            return report
            
        except Exception as e:
            logger.error(f"❌ Corpus processing failed: {e}")
            return {
                'status': 'failed',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    async def get_processing_status(self) -> Dict[str, Any]:
        """Get current processing status"""
        return await get_corpus_processing_status()
    
    async def validate_setup(self) -> Dict[str, Any]:
        """Validate corpus processing setup"""
        
        validation = {
            'dependencies_available': CORPUS_PROCESSING_AVAILABLE,
            'openai_configured': bool(os.getenv('OPENAI_API_KEY')),
            'pinecone_configured': bool(os.getenv('PINECONE_API_KEY')),
            'dataset_accessible': False,
            'vector_engine_ready': False,
            'overall_ready': False
        }
        
        if not CORPUS_PROCESSING_AVAILABLE:
            return validation
        
        try:
            # Test dataset access
            from datasets import load_dataset_builder
            dataset_name = "isaacus/open-australian-legal-corpus"
            
            try:
                builder = load_dataset_builder(dataset_name)
                validation['dataset_accessible'] = True
                logger.info("✅ Legal corpus dataset accessible")
            except Exception as e:
                logger.error(f"❌ Dataset access failed: {e}")
        
            # Test vector engine
            try:
                from vector_search_engine import get_vector_search_engine
                engine = await get_vector_search_engine()
                validation['vector_engine_ready'] = engine.is_initialized
                
                if validation['vector_engine_ready']:
                    logger.info("✅ Vector search engine ready")
                else:
                    logger.error("❌ Vector search engine not initialized")
                    
            except Exception as e:
                logger.error(f"❌ Vector engine validation failed: {e}")
        
        except Exception as e:
            logger.error(f"Validation error: {e}")
        
        # Overall readiness
        validation['overall_ready'] = all([
            validation['dependencies_available'],
            validation['openai_configured'],
            validation['pinecone_configured'],
            validation['vector_engine_ready']
        ])
        
        return validation
    
    def _get_checkpoint_path(self) -> str:
        """Get checkpoint file path"""
        checkpoints_dir = Path('data/checkpoints')
        checkpoints_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return str(checkpoints_dir / f'corpus_processing_{timestamp}.json')
    
    def _print_processing_summary(self, report: Dict[str, Any]):
        """Print formatted processing summary"""
        
        metrics = report['metrics']
        
        logger.info("📊 Processing Summary:")
        logger.info(f"   📋 Total Documents: {metrics['total_documents']:,}")
        logger.info(f"   ✅ Processed: {metrics['processed_documents']:,}")
        logger.info(f"   ❌ Failed: {metrics['failed_documents']:,}")
        logger.info(f"   ⏭️  Skipped: {metrics['skipped_documents']:,}")
        logger.info(f"   📈 Success Rate: {metrics['success_rate']:.1%}")
        logger.info(f"   ⏱️  Processing Time: {metrics['processing_time']:.1f}s")
        logger.info(f"   🚀 Speed: {metrics['processing_speed']:.1f} docs/sec")
        logger.info(f"   🧠 Embeddings Generated: {metrics['embeddings_generated']:,}")
        logger.info(f"   📝 Total Tokens: {metrics['total_tokens']:,}")

async def main():
    """Main corpus processing script"""
    
    parser = argparse.ArgumentParser(
        description='AusLex AI Legal Corpus Processing',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        'command',
        choices=['process', 'status', 'validate'],
        help='Command to execute'
    )
    
    parser.add_argument(
        '--batch-size',
        type=int,
        default=100,
        help='Number of documents to process per batch'
    )
    
    parser.add_argument(
        '--start-index',
        type=int,
        default=0,
        help='Starting document index'
    )
    
    parser.add_argument(
        '--max-documents',
        type=int,
        help='Maximum number of documents to process'
    )
    
    parser.add_argument(
        '--dataset',
        default="isaacus/open-australian-legal-corpus",
        help='HuggingFace dataset name'
    )
    
    parser.add_argument(
        '--checkpoint-file',
        help='Checkpoint file to resume from'
    )
    
    parser.add_argument(
        '--no-checkpoints',
        action='store_true',
        help='Disable checkpoint saving'
    )
    
    parser.add_argument(
        '--json-output',
        action='store_true',
        help='Output results as JSON'
    )
    
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Suppress detailed output'
    )
    
    args = parser.parse_args()
    
    if args.quiet:
        logging.getLogger().setLevel(logging.WARNING)
    
    # Initialize manager
    manager = CorpusProcessingManager()
    
    if args.command in ['process', 'status']:
        success = await manager.initialize()
        if not success:
            logger.error("Failed to initialize corpus processing manager")
            sys.exit(1)
    
    try:
        if args.command == 'validate':
            result = await manager.validate_setup()
            
            if args.json_output:
                print(json.dumps(result, indent=2))
            else:
                logger.info("🔍 Corpus Processing Validation Results:")
                for key, value in result.items():
                    emoji = "✅" if value else "❌"
                    logger.info(f"   {emoji} {key.replace('_', ' ').title()}: {value}")
                
                if result['overall_ready']:
                    logger.info("🎉 System ready for corpus processing!")
                else:
                    logger.error("❌ System not ready - address issues above")
        
        elif args.command == 'status':
            result = await manager.get_processing_status()
            
            if args.json_output:
                print(json.dumps(result, indent=2))
            else:
                logger.info("📊 Current Processing Status:")
                if 'error' in result:
                    logger.error(f"❌ Error: {result['error']}")
                else:
                    performance = result.get('performance', {})
                    logger.info(f"   Success Rate: {performance.get('success_rate', 0):.1%}")
                    logger.info(f"   Processing Speed: {performance.get('processing_speed', 0):.1f} docs/sec")
        
        elif args.command == 'process':
            result = await manager.process_corpus(
                batch_size=args.batch_size,
                start_index=args.start_index,
                max_documents=args.max_documents,
                dataset_name=args.dataset,
                checkpoint_file=args.checkpoint_file,
                save_checkpoints=not args.no_checkpoints
            )
            
            if args.json_output:
                print(json.dumps(result, indent=2))
            
            if result.get('status') != 'completed':
                sys.exit(1)
    
    except Exception as e:
        logger.error(f"Command execution failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())