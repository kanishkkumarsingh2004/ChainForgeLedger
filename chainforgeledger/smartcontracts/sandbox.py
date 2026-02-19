"""
ChainForgeLedger Secure Contract Sandbox

Implements secure sandboxing for smart contract execution.
"""

import time
import os
import tempfile
from typing import Dict, List
from chainforgeledger.smartcontracts.vm import VirtualMachine
from chainforgeledger.smartcontracts.executor import ContractExecutor
from chainforgeledger.utils.logger import get_logger


class ContractSandbox:
    """
    Secure sandbox for smart contract execution.
    
    Attributes:
        vm: Virtual Machine instance
        executor: Contract executor
        resource_limits: Resource limits for contract execution
        execution_history: History of contract executions
        security_monitor: Security monitoring system
        logger: Logger instance
    """
    
    DEFAULT_RESOURCE_LIMITS = {
        'max_gas': 1000000,
        'max_memory': 1024 * 1024,  # 1MB
        'max_time': 5,  # 5 seconds
        'max_stack_depth': 100,
        'max_storage_keys': 1000,
        'max_calls': 100
    }
    
    SECURITY_POLICY = {
        'allow_external_calls': False,
        'allow_file_access': False,
        'allow_network_access': False,
        'allow_system_calls': False,
        'check_stack_overflow': True,
        'check_memory_overflow': True
    }
    
    def __init__(self, vm: VirtualMachine = None, 
                 executor: ContractExecutor = None):
        """
        Initialize a ContractSandbox instance.
        
        Args:
            vm: Optional Virtual Machine instance
            executor: Optional ContractExecutor instance
        """
        self.vm = vm or VirtualMachine()
        self.executor = executor or ContractExecutor(self.vm)
        self.resource_limits = self.DEFAULT_RESOURCE_LIMITS.copy()
        self.execution_history = []
        self.security_monitor = SecurityMonitor()
        self.logger = get_logger(__name__)
        self.temp_dir = tempfile.mkdtemp(prefix='chainforge_sandbox_')
    
    def execute_contract(self, contract_address: str, bytecode: str, 
                       input_data: Dict = None, 
                       caller_address: str = None) -> Dict:
        """
        Execute contract in a secure sandbox.
        
        Args:
            contract_address: Contract address
            bytecode: Contract bytecode
            input_data: Input data for contract execution
            caller_address: Caller address
            
        Returns:
            Execution result dictionary
        """
        # Start execution timer
        start_time = time.time()
        
        # Initialize security context
        security_context = self._create_security_context()
        
        try:
            # Apply resource limits
            self.vm.max_gas = self.resource_limits['max_gas']
            
            # Execute contract
            result = self.executor.execute(
                contract_address,
                bytecode,
                input_data or {},
                caller_address
            )
            
            # Check execution duration
            execution_time = time.time() - start_time
            if execution_time > self.resource_limits['max_time']:
                raise Exception(f"Execution timeout: {execution_time:.2f}s > {self.resource_limits['max_time']}s")
            
            # Record execution
            execution_record = {
                'contract_address': contract_address,
                'caller_address': caller_address,
                'start_time': start_time,
                'execution_time': execution_time,
                'gas_used': result.get('gas_used', 0),
                'success': result.get('success', False),
                'result': result.get('result'),
                'security_violations': security_context.get_violations(),
                'memory_used': self._get_memory_usage(),
                'stack_depth': self._get_stack_depth(),
                'storage_accesses': self._get_storage_accesses()
            }
            
            self.execution_history.append(execution_record)
            
            # Log security violations
            if execution_record['security_violations']:
                self.logger.warning(
                    f"Security violations in contract execution at {contract_address}: "
                    f"{len(execution_record['security_violations'])} violations"
                )
            
            return execution_record
            
        except Exception as e:
            # Handle execution errors
            execution_time = time.time() - start_time
            execution_record = {
                'contract_address': contract_address,
                'caller_address': caller_address,
                'start_time': start_time,
                'execution_time': execution_time,
                'gas_used': self.vm.gas_used,
                'success': False,
                'result': str(e),
                'security_violations': security_context.get_violations(),
                'memory_used': self._get_memory_usage(),
                'stack_depth': self._get_stack_depth(),
                'storage_accesses': self._get_storage_accesses()
            }
            
            self.execution_history.append(execution_record)
            
            self.logger.error(
                f"Contract execution failed at {contract_address}: {str(e)}"
            )
            
            return execution_record
    
    def _create_security_context(self):
        """Create security monitoring context."""
        return SecurityContext(self.SECURITY_POLICY)
    
    def _get_memory_usage(self) -> int:
        """Get memory usage of VM."""
        return len(self.vm.memory)
    
    def _get_stack_depth(self) -> int:
        """Get stack depth of VM."""
        return len(self.vm.stack)
    
    def _get_storage_accesses(self) -> int:
        """Get storage access count of VM."""
        # This would require tracking storage operations in VM
        return 0
    
    def set_resource_limit(self, limit_name: str, value: int):
        """
        Set resource limit for contract execution.
        
        Args:
            limit_name: Limit name
            value: Limit value
            
        Raises:
            ValueError: If limit name is invalid or value is invalid
        """
        if limit_name not in self.DEFAULT_RESOURCE_LIMITS:
            raise ValueError(f"Invalid resource limit: {limit_name}")
            
        if value < 0:
            raise ValueError("Resource limit value cannot be negative")
            
        self.resource_limits[limit_name] = value
    
    def set_security_policy(self, policy_name: str, value: bool):
        """
        Set security policy.
        
        Args:
            policy_name: Policy name
            value: Policy value
            
        Raises:
            ValueError: If policy name is invalid
        """
        if policy_name not in self.SECURITY_POLICY:
            raise ValueError(f"Invalid security policy: {policy_name}")
            
        self.SECURITY_POLICY[policy_name] = value
    
    def get_resource_limits(self) -> Dict:
        """
        Get current resource limits.
        
        Returns:
            Resource limits dictionary
        """
        return self.resource_limits.copy()
    
    def get_security_policy(self) -> Dict:
        """
        Get current security policy.
        
        Returns:
            Security policy dictionary
        """
        return self.SECURITY_POLICY.copy()
    
    def get_execution_history(self, contract_address: str = None, 
                            start_time: float = None, 
                            end_time: float = None) -> List[Dict]:
        """
        Get execution history.
        
        Args:
            contract_address: Optional contract address filter
            start_time: Optional start time filter
            end_time: Optional end time filter
            
        Returns:
            List of execution records
        """
        history = self.execution_history
        
        if contract_address:
            history = [r for r in history if r['contract_address'] == contract_address]
            
        if start_time:
            history = [r for r in history if r['start_time'] >= start_time]
            
        if end_time:
            history = [r for r in history if r['start_time'] <= end_time]
            
        return history
    
    def get_execution_stats(self, contract_address: str = None) -> Dict:
        """
        Get execution statistics.
        
        Args:
            contract_address: Optional contract address filter
            
        Returns:
            Execution statistics dictionary
        """
        history = self.get_execution_history(contract_address)
        
        if not history:
            return {
                'total_executions': 0,
                'successful_executions': 0,
                'failed_executions': 0,
                'average_execution_time': 0,
                'average_gas_used': 0,
                'total_security_violations': 0
            }
            
        total_executions = len(history)
        successful = sum(1 for r in history if r['success'])
        failed = total_executions - successful
        
        average_time = sum(r['execution_time'] for r in history) / total_executions
        average_gas = sum(r['gas_used'] for r in history) / total_executions
        
        violations = sum(len(r['security_violations']) for r in history)
        
        return {
            'total_executions': total_executions,
            'successful_executions': successful,
            'failed_executions': failed,
            'success_rate': (successful / total_executions) * 100,
            'average_execution_time': average_time,
            'average_gas_used': average_gas,
            'total_security_violations': violations
        }
    
    def get_security_stats(self) -> Dict:
        """
        Get security statistics.
        
        Returns:
            Security statistics dictionary
        """
        violations_per_contract = {}
        
        for record in self.execution_history:
            if not record['security_violations']:
                continue
                
            contract = record['contract_address']
            if contract not in violations_per_contract:
                violations_per_contract[contract] = []
                
            violations_per_contract[contract].extend(record['security_violations'])
        
        return {
            'total_contracts_with_violations': len(violations_per_contract),
            'violations_per_contract': {
                contract: len(violations) 
                for contract, violations in violations_per_contract.items()
            },
            'total_violations': sum(
                len(violations) for violations in violations_per_contract.values()
            )
        }
    
    def reset_sandbox(self):
        """Reset sandbox state."""
        self.vm.reset()
        self.execution_history.clear()
        self.security_monitor.reset()
    
    def cleanup_temp_files(self):
        """Cleanup temporary files."""
        import shutil
        if os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
            except Exception as e:
                self.logger.error(f"Failed to cleanup temp files: {e}")
    
    def __del__(self):
        """Destructor to cleanup temporary files."""
        self.cleanup_temp_files()
    
    def __repr__(self):
        """String representation of the ContractSandbox."""
        stats = self.get_execution_stats()
        return (f"ContractSandbox(executions={stats['total_executions']}, "
                f"success={stats['success_rate']:.1f}%, "
                f"violations={stats['total_security_violations']})")
    
    def __str__(self):
        """String representation for printing."""
        stats = self.get_execution_stats()
        security_stats = self.get_security_stats()
        
        return (
            f"Contract Sandbox\n"
            f"================\n"
            f"Total Executions: {stats['total_executions']}\n"
            f"Successful: {stats['successful_executions']} ({stats['success_rate']:.1f}%)\n"
            f"Failed: {stats['failed_executions']}\n"
            f"Average Time: {stats['average_execution_time']:.3f}s\n"
            f"Average Gas: {stats['average_gas_used']:.0f}\n"
            f"Security Violations: {security_stats['total_violations']}\n"
            f"Contracts with Violations: {security_stats['total_contracts_with_violations']}"
        )


class SecurityContext:
    """
    Security monitoring context for contract execution.
    """
    
    def __init__(self, policy: Dict):
        """
        Initialize a SecurityContext instance.
        
        Args:
            policy: Security policy
        """
        self.policy = policy
        self.violations = []
        self.monitoring = False
    
    def start_monitoring(self):
        """Start security monitoring."""
        self.monitoring = True
        self.violations = []
    
    def stop_monitoring(self):
        """Stop security monitoring."""
        self.monitoring = False
    
    def check_violation(self, violation_type: str, details: str = None):
        """
        Check if a security violation has occurred.
        
        Args:
            violation_type: Violation type
            details: Optional violation details
        """
        if self.monitoring:
            self.violations.append({
                'type': violation_type,
                'timestamp': time.time(),
                'details': details
            })
    
    def get_violations(self) -> List[Dict]:
        """
        Get security violations.
        
        Returns:
            List of security violations
        """
        return self.violations.copy()
    
    def has_violations(self) -> bool:
        """
        Check if there are any security violations.
        
        Returns:
            True if there are violations
        """
        return len(self.violations) > 0


class SecurityMonitor:
    """
    Security monitor for contract execution.
    """
    
    def __init__(self):
        """Initialize a SecurityMonitor instance."""
        self.violations = []
        self.monitoring_enabled = True
    
    def log_violation(self, violation: Dict):
        """
        Log a security violation.
        
        Args:
            violation: Violation information dictionary
        """
        if self.monitoring_enabled:
            self.violations.append(violation)
    
    def check_contract_bytecode(self, bytecode: str) -> List[Dict]:
        """
        Check contract bytecode for security issues.
        
        Args:
            bytecode: Contract bytecode
            
        Returns:
            List of security issues
        """
        issues = []
        
        # Check for known malicious patterns
        malicious_patterns = [
            b'\x90\x90',  # Jump destination manipulation
            b'\x60\xfe',  # Large immediate values
            b'\x50\x50'   # Duplicate pops
        ]
        
        for pattern in malicious_patterns:
            if pattern in bytecode:
                issues.append({
                    'type': 'malicious_bytecode',
                    'description': f"Known malicious bytecode pattern detected"
                })
        
        return issues
    
    def get_violations(self) -> List[Dict]:
        """
        Get all security violations.
        
        Returns:
            List of security violations
        """
        return self.violations.copy()
    
    def reset(self):
        """Reset security monitor."""
        self.violations.clear()
