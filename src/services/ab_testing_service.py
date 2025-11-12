"""
A/B Testing Framework
Feature flags and experiment management
Version: v8.4.0
"""

import logging
import hashlib
import random
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class ExperimentStatus(str, Enum):
    """Experiment status"""
    DRAFT = 'draft'
    ACTIVE = 'active'
    PAUSED = 'paused'
    COMPLETED = 'completed'


class Variant(str, Enum):
    """Experiment variants"""
    CONTROL = 'control'
    VARIANT_A = 'variant_a'
    VARIANT_B = 'variant_b'
    VARIANT_C = 'variant_c'


class ABTestingService:
    """A/B testing and feature flag service"""

    def __init__(self):
        """Initialize A/B testing service"""
        self.experiments: Dict[str, Dict[str, Any]] = {}
        self.feature_flags: Dict[str, bool] = {}
        self.user_assignments: Dict[str, Dict[str, str]] = {}

    def create_experiment(
        self,
        experiment_id: str,
        name: str,
        description: str,
        variants: Dict[str, float],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Create new A/B test experiment

        Args:
            experiment_id: Unique experiment ID
            name: Experiment name
            description: Experiment description
            variants: Dict of variant names and traffic allocation percentages
                     Example: {'control': 0.5, 'variant_a': 0.5}
            start_date: Experiment start date
            end_date: Experiment end date

        Returns:
            Experiment configuration
        """
        # Validate traffic allocation
        total_traffic = sum(variants.values())
        if not 0.99 <= total_traffic <= 1.01:
            raise ValueError(f'Traffic allocation must sum to 1.0, got {total_traffic}')

        experiment = {
            'id': experiment_id,
            'name': name,
            'description': description,
            'variants': variants,
            'status': ExperimentStatus.DRAFT,
            'start_date': start_date.isoformat() if start_date else None,
            'end_date': end_date.isoformat() if end_date else None,
            'created_at': datetime.now().isoformat(),
            'metrics': {},
        }

        self.experiments[experiment_id] = experiment
        logger.info(f'Created experiment: {experiment_id}')

        return experiment

    def start_experiment(self, experiment_id: str) -> bool:
        """Start experiment"""
        if experiment_id not in self.experiments:
            return False

        self.experiments[experiment_id]['status'] = ExperimentStatus.ACTIVE
        logger.info(f'Started experiment: {experiment_id}')
        return True

    def stop_experiment(self, experiment_id: str) -> bool:
        """Stop experiment"""
        if experiment_id not in self.experiments:
            return False

        self.experiments[experiment_id]['status'] = ExperimentStatus.COMPLETED
        logger.info(f'Stopped experiment: {experiment_id}')
        return True

    def assign_variant(
        self,
        experiment_id: str,
        user_id: str,
        force_variant: Optional[str] = None
    ) -> str:
        """
        Assign user to experiment variant

        Args:
            experiment_id: Experiment ID
            user_id: User ID
            force_variant: Force specific variant (for testing)

        Returns:
            Assigned variant name
        """
        if experiment_id not in self.experiments:
            return 'control'

        experiment = self.experiments[experiment_id]

        # Check if experiment is active
        if experiment['status'] != ExperimentStatus.ACTIVE:
            return 'control'

        # Check if user already assigned
        if user_id in self.user_assignments.get(experiment_id, {}):
            return self.user_assignments[experiment_id][user_id]

        # Force variant if specified
        if force_variant and force_variant in experiment['variants']:
            variant = force_variant
        else:
            # Deterministic assignment based on hash
            variant = self._hash_assign(user_id, experiment_id, experiment['variants'])

        # Store assignment
        if experiment_id not in self.user_assignments:
            self.user_assignments[experiment_id] = {}

        self.user_assignments[experiment_id][user_id] = variant

        logger.debug(f'Assigned {user_id} to {variant} in {experiment_id}')
        return variant

    def _hash_assign(
        self,
        user_id: str,
        experiment_id: str,
        variants: Dict[str, float]
    ) -> str:
        """
        Deterministically assign variant using hash

        Args:
            user_id: User ID
            experiment_id: Experiment ID
            variants: Variant traffic allocation

        Returns:
            Assigned variant name
        """
        # Create deterministic hash
        hash_input = f'{experiment_id}:{user_id}'
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)

        # Normalize to 0-1
        normalized = (hash_value % 10000) / 10000.0

        # Assign variant based on traffic allocation
        cumulative = 0.0
        for variant_name, traffic in variants.items():
            cumulative += traffic
            if normalized <= cumulative:
                return variant_name

        # Fallback to control
        return 'control'

    def get_variant(self, experiment_id: str, user_id: str) -> Optional[str]:
        """Get user's assigned variant"""
        return self.user_assignments.get(experiment_id, {}).get(user_id)

    def track_metric(
        self,
        experiment_id: str,
        user_id: str,
        metric_name: str,
        value: float
    ):
        """
        Track experiment metric

        Args:
            experiment_id: Experiment ID
            user_id: User ID
            metric_name: Metric name (e.g., 'conversion', 'click_rate')
            value: Metric value
        """
        if experiment_id not in self.experiments:
            return

        variant = self.get_variant(experiment_id, user_id)
        if not variant:
            return

        # Initialize metrics structure
        if 'metrics' not in self.experiments[experiment_id]:
            self.experiments[experiment_id]['metrics'] = {}

        if metric_name not in self.experiments[experiment_id]['metrics']:
            self.experiments[experiment_id]['metrics'][metric_name] = {}

        if variant not in self.experiments[experiment_id]['metrics'][metric_name]:
            self.experiments[experiment_id]['metrics'][metric_name][variant] = {
                'values': [],
                'count': 0,
                'sum': 0,
                'mean': 0,
            }

        # Update metrics
        variant_metrics = self.experiments[experiment_id]['metrics'][metric_name][variant]
        variant_metrics['values'].append(value)
        variant_metrics['count'] += 1
        variant_metrics['sum'] += value
        variant_metrics['mean'] = variant_metrics['sum'] / variant_metrics['count']

        logger.debug(f'Tracked {metric_name}={value} for {variant} in {experiment_id}')

    def get_experiment_results(self, experiment_id: str) -> Dict[str, Any]:
        """
        Get experiment results

        Args:
            experiment_id: Experiment ID

        Returns:
            Experiment results with metrics by variant
        """
        if experiment_id not in self.experiments:
            return {}

        experiment = self.experiments[experiment_id]

        # Calculate summary statistics
        results = {
            'experiment_id': experiment_id,
            'name': experiment['name'],
            'status': experiment['status'],
            'variants': {},
        }

        for variant_name in experiment['variants'].keys():
            variant_results = {
                'traffic_allocation': experiment['variants'][variant_name],
                'assigned_users': sum(1 for v in self.user_assignments.get(experiment_id, {}).values() if v == variant_name),
                'metrics': {},
            }

            # Add metrics
            for metric_name, metric_data in experiment.get('metrics', {}).items():
                if variant_name in metric_data:
                    variant_results['metrics'][metric_name] = {
                        'mean': metric_data[variant_name]['mean'],
                        'count': metric_data[variant_name]['count'],
                        'sum': metric_data[variant_name]['sum'],
                    }

            results['variants'][variant_name] = variant_results

        return results

    def set_feature_flag(self, flag_name: str, enabled: bool):
        """Set feature flag"""
        self.feature_flags[flag_name] = enabled
        logger.info(f'Feature flag {flag_name} set to {enabled}')

    def is_feature_enabled(
        self,
        flag_name: str,
        user_id: Optional[str] = None,
        default: bool = False
    ) -> bool:
        """
        Check if feature is enabled

        Args:
            flag_name: Feature flag name
            user_id: User ID (for user-specific flags)
            default: Default value if flag not found

        Returns:
            Feature enabled status
        """
        return self.feature_flags.get(flag_name, default)

    def get_all_experiments(self, status: Optional[ExperimentStatus] = None) -> List[Dict[str, Any]]:
        """Get all experiments, optionally filtered by status"""
        experiments = list(self.experiments.values())

        if status:
            experiments = [e for e in experiments if e['status'] == status]

        return experiments


# Singleton instance
_ab_testing_service = None


def get_ab_testing_service() -> ABTestingService:
    """Get A/B testing service singleton"""
    global _ab_testing_service
    if _ab_testing_service is None:
        _ab_testing_service = ABTestingService()
    return _ab_testing_service
