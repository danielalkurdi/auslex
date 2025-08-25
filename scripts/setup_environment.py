#!/usr/bin/env python3
"""
Environment Setup and Validation Script for AusLex AI System
Validates API keys, dependencies, and initializes vector database
"""

import os
import sys
import json
import asyncio
import logging
import time
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import subprocess
import importlib
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EnvironmentValidator:
    """Validates and sets up the AusLex AI environment"""
    
    def __init__(self):
        self.validation_results = {
            'python_environment': False,
            'dependencies': False,
            'openai_api': False,
            'pinecone_api': False,
            'vector_database': False,
            'legal_corpus': False,
            'compliance_system': False,
            'overall_status': False
        }
        
        self.required_env_vars = {
            'OPENAI_API_KEY': 'OpenAI API key for embeddings and chat completions',
            'PINECONE_API_KEY': 'Pinecone API key for vector database',
            'PINECONE_ENVIRONMENT': 'Pinecone environment (e.g., us-east1-aws)',
            'PINECONE_INDEX_NAME': 'Pinecone index name for legal corpus'
        }
        
        self.optional_env_vars = {
            'OPENAI_BASE_URL': 'Custom OpenAI API endpoint',
            'OPENAI_ORG': 'OpenAI organization ID',
            'OPENAI_PROJECT': 'OpenAI project ID',
            'EMBEDDING_DIMENSIONS': 'Embedding dimensions (default: 1536)',
            'SEARCH_TOP_K': 'Default search result count (default: 10)',
            'SIMILARITY_THRESHOLD': 'Minimum similarity threshold (default: 0.75)'
        }
        
        self.required_packages = [
            'fastapi>=0.104.1',
            'openai>=1.35.7',
            'pinecone-client>=3.0.0',
            'scikit-learn>=1.5.1',
            'datasets>=2.14.6',
            'numpy>=1.24.3',
            'pandas>=2.0.3',
            'pydantic>=2.5.0',
            'httpx>=0.27.0'
        ]
    
    async def run_full_validation(self) -> Dict[str, Any]:
        """Run complete environment validation"""
        
        logger.info("🚀 Starting AusLex AI Environment Validation")
        logger.info("=" * 60)
        
        start_time = time.time()
        
        # Step 1: Python environment
        logger.info("1️⃣ Validating Python environment...")
        self.validation_results['python_environment'] = self._validate_python_environment()
        
        # Step 2: Dependencies
        logger.info("2️⃣ Validating dependencies...")
        self.validation_results['dependencies'] = await self._validate_dependencies()
        
        # Step 3: Environment variables
        logger.info("3️⃣ Validating environment variables...")
        env_validation = self._validate_environment_variables()
        
        # Step 4: OpenAI API
        logger.info("4️⃣ Validating OpenAI API connection...")
        self.validation_results['openai_api'] = await self._validate_openai_api()
        
        # Step 5: Pinecone API
        logger.info("5️⃣ Validating Pinecone API connection...")
        self.validation_results['pinecone_api'] = await self._validate_pinecone_api()
        
        # Step 6: Vector database setup
        logger.info("6️⃣ Validating vector database setup...")
        self.validation_results['vector_database'] = await self._validate_vector_database()
        
        # Step 7: Legal corpus access
        logger.info("7️⃣ Validating legal corpus access...")
        self.validation_results['legal_corpus'] = await self._validate_legal_corpus()
        
        # Step 8: Compliance system
        logger.info("8️⃣ Validating legal compliance system...")
        self.validation_results['compliance_system'] = await self._validate_compliance_system()
        
        # Overall status
        self.validation_results['overall_status'] = all([
            self.validation_results['python_environment'],
            self.validation_results['dependencies'],
            self.validation_results['openai_api'],
            self.validation_results['pinecone_api']
        ])
        
        end_time = time.time()
        
        logger.info("=" * 60)
        logger.info(f"✅ Validation completed in {end_time - start_time:.1f} seconds")
        
        return self._generate_validation_report()
    
    def _validate_python_environment(self) -> bool:
        """Validate Python version and basic environment"""
        try:
            python_version = sys.version_info
            
            if python_version.major != 3 or python_version.minor < 9:
                logger.error(f"❌ Python 3.9+ required, found {python_version.major}.{python_version.minor}")
                return False
            
            logger.info(f"✅ Python {python_version.major}.{python_version.minor}.{python_version.micro}")
            
            # Check virtual environment
            if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
                logger.info("✅ Virtual environment detected")
            else:
                logger.warning("⚠️  No virtual environment detected (recommended)")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Python environment validation failed: {e}")
            return False
    
    async def _validate_dependencies(self) -> bool:
        """Validate required Python packages"""
        try:
            missing_packages = []
            
            for package in self.required_packages:
                package_name = package.split('>=')[0].split('==')[0]
                
                try:
                    importlib.import_module(package_name.replace('-', '_'))
                    logger.info(f"✅ {package_name}")
                except ImportError:
                    missing_packages.append(package)
                    logger.error(f"❌ {package_name} - not installed")
            
            if missing_packages:
                logger.error("Missing packages can be installed with:")
                logger.error(f"pip install {' '.join(missing_packages)}")
                return False
            
            logger.info("✅ All required dependencies installed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Dependency validation failed: {e}")
            return False
    
    def _validate_environment_variables(self) -> Dict[str, Any]:
        """Validate environment variables"""
        
        results = {'required': {}, 'optional': {}, 'missing_required': []}
        
        # Check required variables
        for var, description in self.required_env_vars.items():
            value = os.getenv(var)
            if value:
                # Mask sensitive values
                display_value = value[:8] + '...' if len(value) > 8 else value
                results['required'][var] = {'value': display_value, 'description': description}
                logger.info(f"✅ {var}: {display_value}")
            else:
                results['missing_required'].append(var)
                logger.error(f"❌ {var}: Missing - {description}")
        
        # Check optional variables
        for var, description in self.optional_env_vars.items():
            value = os.getenv(var)
            if value:
                results['optional'][var] = {'value': value, 'description': description}
                logger.info(f"✅ {var}: {value}")
            else:
                logger.info(f"ℹ️  {var}: Not set - {description}")
        
        return results
    
    async def _validate_openai_api(self) -> bool:
        """Validate OpenAI API connection and permissions"""
        try:
            # Add API directory to path for imports
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'api'))
            
            from openai import OpenAI
            
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                logger.error("❌ OpenAI API key not configured")
                return False
            
            # Initialize client
            client_kwargs = {'api_key': api_key}
            
            if os.getenv('OPENAI_BASE_URL'):
                client_kwargs['base_url'] = os.getenv('OPENAI_BASE_URL')
            if os.getenv('OPENAI_ORG'):
                client_kwargs['organization'] = os.getenv('OPENAI_ORG')
            if os.getenv('OPENAI_PROJECT'):
                client_kwargs['project'] = os.getenv('OPENAI_PROJECT')
            
            client = OpenAI(**client_kwargs)
            
            # Test embeddings API
            test_response = client.embeddings.create(
                model="text-embedding-3-small",
                input="Test embedding for AusLex AI validation"
            )
            
            if test_response.data and len(test_response.data) > 0:
                embedding_dim = len(test_response.data[0].embedding)
                logger.info(f"✅ OpenAI Embeddings API - {embedding_dim} dimensions")
            
            # Test chat API
            chat_response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": "Hello, this is a test."}],
                max_tokens=10
            )
            
            if chat_response.choices and chat_response.choices[0].message.content:
                logger.info("✅ OpenAI Chat Completions API")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ OpenAI API validation failed: {e}")
            return False
    
    async def _validate_pinecone_api(self) -> bool:
        """Validate Pinecone API connection"""
        try:
            from pinecone import Pinecone
            
            api_key = os.getenv('PINECONE_API_KEY')
            if not api_key:
                logger.error("❌ Pinecone API key not configured")
                return False
            
            # Initialize Pinecone client
            pc = Pinecone(api_key=api_key)
            
            # List indexes to test connection
            indexes = pc.list_indexes()
            logger.info(f"✅ Pinecone API connected - {len(indexes)} indexes available")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Pinecone API validation failed: {e}")
            return False
    
    async def _validate_vector_database(self) -> bool:
        """Validate vector database setup"""
        try:
            from pinecone import Pinecone, ServerlessSpec
            
            api_key = os.getenv('PINECONE_API_KEY')
            index_name = os.getenv('PINECONE_INDEX_NAME', 'auslex-legal-corpus')
            environment = os.getenv('PINECONE_ENVIRONMENT', 'us-east1-aws')
            
            if not api_key:
                return False
            
            pc = Pinecone(api_key=api_key)
            
            # Check if index exists
            existing_indexes = [idx.name for idx in pc.list_indexes()]
            
            if index_name in existing_indexes:
                logger.info(f"✅ Vector index '{index_name}' exists")
                
                # Check index stats
                index = pc.Index(index_name)
                stats = index.describe_index_stats()
                
                logger.info(f"✅ Index statistics:")
                logger.info(f"   - Total vectors: {stats.total_vector_count:,}")
                logger.info(f"   - Dimension: {stats.dimension}")
                
                if stats.total_vector_count > 0:
                    logger.info("✅ Index contains data")
                else:
                    logger.warning("⚠️  Index is empty - run corpus processing")
                
            else:
                logger.warning(f"⚠️  Vector index '{index_name}' does not exist")
                logger.info("Will create index during corpus processing")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Vector database validation failed: {e}")
            return False
    
    async def _validate_legal_corpus(self) -> bool:
        """Validate access to legal corpus dataset"""
        try:
            # Test HuggingFace datasets access
            from datasets import load_dataset_builder
            
            dataset_name = "isaacus/open-australian-legal-corpus"
            
            # Get dataset info without downloading
            dataset_builder = load_dataset_builder(dataset_name)
            info = dataset_builder.info
            
            logger.info(f"✅ Legal corpus accessible: {dataset_name}")
            if hasattr(info, 'splits') and info.splits:
                total_docs = sum(split.num_examples for split in info.splits.values())
                logger.info(f"   - Total documents: {total_docs:,}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Legal corpus validation failed: {e}")
            logger.info("Note: Corpus will be downloaded during first processing")
            return False
    
    async def _validate_compliance_system(self) -> bool:
        """Validate legal compliance system"""
        try:
            # Test import of compliance components
            from legal_compliance import (
                LegalComplianceValidator,
                ComplianceLevel,
                validate_legal_response
            )
            
            # Test basic compliance validation
            validator = LegalComplianceValidator()
            
            # Test prohibited language detection
            test_response = "The Migration Act 1958 establishes character test requirements."
            test_query = "What is the character test?"
            
            validation_result = await validate_legal_response(test_response, test_query)
            
            if 'overall_compliance' in validation_result:
                compliance_level = validation_result['overall_compliance']
                logger.info(f"✅ Legal compliance system - Risk level: {compliance_level}")
                return True
            else:
                logger.error("❌ Compliance validation returned invalid result")
                return False
            
        except Exception as e:
            logger.error(f"❌ Legal compliance system validation failed: {e}")
            return False
    
    def _generate_validation_report(self) -> Dict[str, Any]:
        """Generate comprehensive validation report"""
        
        report = {
            'timestamp': datetime.utcnow().isoformat(),
            'overall_status': self.validation_results['overall_status'],
            'validation_results': self.validation_results,
            'system_info': {
                'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                'platform': sys.platform,
                'working_directory': os.getcwd()
            },
            'recommendations': [],
            'next_steps': []
        }
        
        # Generate recommendations based on results
        if not self.validation_results['openai_api']:
            report['recommendations'].append("Configure OPENAI_API_KEY environment variable")
        
        if not self.validation_results['pinecone_api']:
            report['recommendations'].append("Configure PINECONE_API_KEY environment variable")
        
        if not self.validation_results['dependencies']:
            report['recommendations'].append("Install missing Python packages")
        
        if not self.validation_results['vector_database']:
            report['recommendations'].append("Set up Pinecone vector database")
        
        # Generate next steps
        if self.validation_results['overall_status']:
            report['next_steps'] = [
                "✅ Environment ready for AusLex AI system",
                "🚀 Run corpus processing: python -m scripts.process_corpus",
                "🧪 Run test suite: python -m pytest tests/python/",
                "🌐 Start development server: npm start"
            ]
        else:
            report['next_steps'] = [
                "❌ Environment setup incomplete",
                "🔧 Address missing requirements above",
                "🔄 Re-run validation: python scripts/setup_environment.py"
            ]
        
        return report
    
    def print_validation_report(self, report: Dict[str, Any]):
        """Print formatted validation report"""
        
        logger.info("\n" + "=" * 60)
        logger.info("🎯 AUSLEX AI VALIDATION REPORT")
        logger.info("=" * 60)
        
        # Overall status
        status_emoji = "✅" if report['overall_status'] else "❌"
        logger.info(f"{status_emoji} Overall Status: {'READY' if report['overall_status'] else 'NEEDS SETUP'}")
        
        logger.info(f"📅 Validation Time: {report['timestamp']}")
        logger.info(f"🐍 Python Version: {report['system_info']['python_version']}")
        
        # Component status
        logger.info("\n📋 Component Status:")
        for component, status in report['validation_results'].items():
            if component == 'overall_status':
                continue
            emoji = "✅" if status else "❌"
            logger.info(f"   {emoji} {component.replace('_', ' ').title()}")
        
        # Recommendations
        if report['recommendations']:
            logger.info("\n💡 Recommendations:")
            for rec in report['recommendations']:
                logger.info(f"   • {rec}")
        
        # Next steps
        logger.info("\n🎯 Next Steps:")
        for step in report['next_steps']:
            logger.info(f"   {step}")
        
        logger.info("\n" + "=" * 60)

async def create_sample_env_file():
    """Create sample .env file with required variables"""
    
    env_template = """# AusLex AI Environment Configuration
# Copy to .env and fill in your actual API keys

# Required: OpenAI API Configuration
OPENAI_API_KEY=sk-your-openai-api-key-here
# OPENAI_BASE_URL=https://api.openai.com/v1  # Optional: custom endpoint
# OPENAI_ORG=your-org-id                     # Optional: organization
# OPENAI_PROJECT=your-project-id             # Optional: project

# Required: Pinecone Vector Database Configuration
PINECONE_API_KEY=your-pinecone-api-key-here
PINECONE_ENVIRONMENT=us-east1-aws
PINECONE_INDEX_NAME=auslex-legal-corpus

# Optional: Vector Search Configuration
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSIONS=1536
SEARCH_TOP_K=10
SIMILARITY_THRESHOLD=0.75
ENABLE_HYBRID_SEARCH=true
ENABLE_METADATA_FILTERING=true

# Optional: API Configuration
ALLOWED_ORIGINS=http://localhost:3000,https://yourdomain.com
JWT_SECRET_KEY=your-jwt-secret-key-here

# Optional: Development Configuration
DEBUG=false
LOG_LEVEL=INFO
"""
    
    env_file = Path('.env.example')
    
    try:
        with open(env_file, 'w') as f:
            f.write(env_template)
        
        logger.info(f"✅ Sample environment file created: {env_file}")
        logger.info("   Copy to .env and configure your API keys")
        
    except Exception as e:
        logger.error(f"❌ Failed to create sample .env file: {e}")

async def main():
    """Main setup and validation script"""
    
    parser = None
    try:
        import argparse
        parser = argparse.ArgumentParser(description='AusLex AI Environment Setup and Validation')
        parser.add_argument('--create-env', action='store_true', help='Create sample .env file')
        parser.add_argument('--json-output', action='store_true', help='Output report as JSON')
        parser.add_argument('--quiet', action='store_true', help='Suppress detailed output')
        args = parser.parse_args()
    except ImportError:
        # Fallback for environments without argparse
        class Args:
            create_env = False
            json_output = False
            quiet = False
        args = Args()
    
    if args.create_env:
        await create_sample_env_file()
        return
    
    if args.quiet:
        logging.getLogger().setLevel(logging.WARNING)
    
    # Run validation
    validator = EnvironmentValidator()
    report = await validator.run_full_validation()
    
    if args.json_output:
        print(json.dumps(report, indent=2))
    else:
        validator.print_validation_report(report)
    
    # Exit with appropriate code
    exit_code = 0 if report['overall_status'] else 1
    sys.exit(exit_code)

if __name__ == "__main__":
    asyncio.run(main())