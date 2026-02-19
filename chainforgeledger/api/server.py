"""
ChainForgeLedger API Server

HTTP server implementation for blockchain API.
"""

import threading
from typing import Any, Dict
from chainforgeledger.utils.logger import get_logger


class ApiServer:
    """
    API server implementation.
    
    Provides REST API endpoints for blockchain operations.
    """
    
    def __init__(self, host: str = "0.0.0.0", port: int = 8080, blockchain: Any = None):
        """
        Initialize API server.
        
        Args:
            host: Server host address
            port: Server port
            blockchain: Blockchain instance
        """
        self.host = host
        self.port = port
        self.blockchain = blockchain
        self.server = None
        self.running = False
        self.thread = None
        self.logger = get_logger(__name__)
        
        # API endpoints
        self.endpoints = {
            "/": {"GET": self.handle_root},
            "/health": {"GET": self.handle_health},
            "/blockchain/blocks": {"GET": self.handle_get_blocks},
            "/blockchain/blocks/<int:index>": {"GET": self.handle_get_block},
            "/blockchain/blocks/<hash>": {"GET": self.handle_get_block_by_hash},
            "/blockchain/blocks/last": {"GET": self.handle_get_last_block},
            "/blockchain/transactions": {"GET": self.handle_get_transactions},
            "/blockchain/transactions/<str:txid>": {"GET": self.handle_get_transaction},
            "/blockchain/mempool": {"GET": self.handle_get_mempool},
            "/blockchain/stats": {"GET": self.handle_get_stats},
            "/blockchain/balance/<address>": {"GET": self.handle_get_balance},
            "/blockchain/address/<address>": {"GET": self.handle_get_address},
            "/blockchain/wallets": {"GET": self.handle_get_wallets},
            "/blockchain/wallets/<address>": {"GET": self.handle_get_wallet},
            "/blockchain/nodes": {"GET": self.handle_get_nodes},
            "/blockchain/nodes/<node_id>": {"GET": self.handle_get_node},
            "/transactions": {"POST": self.handle_create_transaction},
            "/blocks/mine": {"POST": self.handle_mine_block},
            "/contracts": {"POST": self.handle_deploy_contract},
            "/contracts/<address>": {"GET": self.handle_get_contract},
            "/contracts/<address>/execute": {"POST": self.handle_execute_contract}
        }
    
    def handle_root(self, params: Dict) -> Dict:
        """
        Root endpoint.
        
        Args:
            params: Request parameters
            
        Returns:
            Response dictionary
        """
        return {
            "success": True,
            "name": "ChainForgeLedger API",
            "version": "1.0.0",
            "description": "Blockchain API",
            "endpoints": list(self.endpoints.keys())
        }
    
    def handle_health(self, params: Dict) -> Dict:
        """
        Health check endpoint.
        
        Args:
            params: Request parameters
            
        Returns:
            Response dictionary
        """
        return {
            "success": True,
            "status": "healthy",
            "timestamp": self.blockchain.get_current_timestamp(),
            "chain_length": len(self.blockchain.chain) if self.blockchain else 0,
            "name": "ChainForgeLedger"
        }
    
    def handle_get_blocks(self, params: Dict) -> Dict:
        """
        Get all blocks.
        
        Args:
            params: Request parameters
            
        Returns:
            Response dictionary
        """
        try:
            limit = params.get("limit", 100)
            offset = params.get("offset", 0)
            
            blocks = self.blockchain.chain
            
            if offset > len(blocks):
                return {"success": False, "error": "Offset too large"}
            
            end = min(offset + limit, len(blocks))
            blocks_data = [block.to_dict() for block in blocks[offset:end]]
            
            return {
                "success": True,
                "blocks": blocks_data,
                "count": len(blocks_data),
                "total": len(blocks)
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def handle_get_block(self, params: Dict) -> Dict:
        """
        Get block by index.
        
        Args:
            params: Request parameters
            
        Returns:
            Response dictionary
        """
        try:
            index = params.get("index")
            
            if index < 0 or index >= len(self.blockchain.chain):
                return {"success": False, "error": "Block not found"}
            
            block = self.blockchain.chain[index]
            
            return {
                "success": True,
                "block": block.to_dict()
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def handle_get_block_by_hash(self, params: Dict) -> Dict:
        """
        Get block by hash.
        
        Args:
            params: Request parameters
            
        Returns:
            Response dictionary
        """
        try:
            block_hash = params.get("hash")
            
            for block in self.blockchain.chain:
                if block.block_hash == block_hash:
                    return {"success": True, "block": block.to_dict()}
            
            return {"success": False, "error": "Block not found"}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def handle_get_last_block(self, params: Dict) -> Dict:
        """
        Get last block.
        
        Args:
            params: Request parameters
            
        Returns:
            Response dictionary
        """
        try:
            block = self.blockchain.chain[-1]
            
            return {
                "success": True,
                "block": block.to_dict()
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def handle_get_transactions(self, params: Dict) -> Dict:
        """
        Get all transactions.
        
        Args:
            params: Request parameters
            
        Returns:
            Response dictionary
        """
        try:
            limit = params.get("limit", 100)
            offset = params.get("offset", 0)
            
            all_transactions = []
            for block in self.blockchain.chain:
                for tx in block.transactions:
                    all_transactions.append(tx.to_dict())
            
            if offset > len(all_transactions):
                return {"success": False, "error": "Offset too large"}
            
            end = min(offset + limit, len(all_transactions))
            transactions_data = all_transactions[offset:end]
            
            return {
                "success": True,
                "transactions": transactions_data,
                "count": len(transactions_data),
                "total": len(all_transactions)
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def handle_get_transaction(self, params: Dict) -> Dict:
        """
        Get transaction by ID.
        
        Args:
            params: Request parameters
            
        Returns:
            Response dictionary
        """
        try:
            txid = params.get("txid")
            
            for block in self.blockchain.chain:
                for tx in block.transactions:
                    if tx.transaction_id == txid:
                        return {"success": True, "transaction": tx.to_dict()}
            
            return {"success": False, "error": "Transaction not found"}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def handle_get_mempool(self, params: Dict) -> Dict:
        """
        Get mempool transactions.
        
        Args:
            params: Request parameters
            
        Returns:
            Response dictionary
        """
        try:
            transactions = []
            
            if hasattr(self.blockchain, "mempool"):
                transactions = [tx.to_dict() for tx in self.blockchain.mempool.transactions]
            
            return {
                "success": True,
                "transactions": transactions,
                "count": len(transactions)
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def handle_get_stats(self, params: Dict) -> Dict:
        """
        Get blockchain statistics.
        
        Args:
            params: Request parameters
            
        Returns:
            Response dictionary
        """
        try:
            stats = self.blockchain.get_statistics()
            
            return {
                "success": True,
                "stats": stats
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def handle_get_balance(self, params: Dict) -> Dict:
        """
        Get address balance.
        
        Args:
            params: Request parameters
            
        Returns:
            Response dictionary
        """
        try:
            address = params.get("address")
            balance = self.blockchain.get_balance(address)
            
            return {
                "success": True,
                "address": address,
                "balance": balance
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def handle_get_address(self, params: Dict) -> Dict:
        """
        Get address information.
        
        Args:
            params: Request parameters
            
        Returns:
            Response dictionary
        """
        try:
            address = params.get("address")
            balance = self.blockchain.get_balance(address)
            
            transactions = []
            for block in self.blockchain.chain:
                for tx in block.transactions:
                    if tx.sender == address or tx.recipient == address:
                        transactions.append(tx.to_dict())
            
            return {
                "success": True,
                "address": address,
                "balance": balance,
                "transactions": transactions,
                "transaction_count": len(transactions)
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def handle_get_wallets(self, params: Dict) -> Dict:
        """
        Get all wallets.
        
        Args:
            params: Request parameters
            
        Returns:
            Response dictionary
        """
        try:
            if hasattr(self.blockchain, "wallets"):
                return {
                    "success": True,
                    "wallets": self.blockchain.wallets,
                    "count": len(self.blockchain.wallets)
                }
            
            return {
                "success": False,
                "error": "Wallets not available"
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def handle_get_wallet(self, params: Dict) -> Dict:
        """
        Get wallet information.
        
        Args:
            params: Request parameters
            
        Returns:
            Response dictionary
        """
        try:
            address = params.get("address")
            
            if hasattr(self.blockchain, "wallets") and address in self.blockchain.wallets:
                wallet = self.blockchain.wallets[address]
                return {"success": True, "wallet": wallet}
            
            return {"success": False, "error": "Wallet not found"}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def handle_get_nodes(self, params: Dict) -> Dict:
        """
        Get network nodes.
        
        Args:
            params: Request parameters
            
        Returns:
            Response dictionary
        """
        try:
            if hasattr(self.blockchain, "node"):
                nodes = []
                for peer in self.blockchain.node.peers:
                    nodes.append({
                        "id": peer.node_id,
                        "address": peer.address,
                        "port": peer.port,
                        "connected": peer.is_connected
                    })
                
                return {
                    "success": True,
                    "nodes": nodes,
                    "count": len(nodes)
                }
            
            return {"success": False, "error": "Node information not available"}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def handle_get_node(self, params: Dict) -> Dict:
        """
        Get node information.
        
        Args:
            params: Request parameters
            
        Returns:
            Response dictionary
        """
        try:
            node_id = params.get("node_id")
            
            if hasattr(self.blockchain, "node"):
                for peer in self.blockchain.node.peers:
                    if peer.node_id == node_id:
                        return {
                            "success": True,
                            "node": {
                                "id": peer.node_id,
                                "address": peer.address,
                                "port": peer.port,
                                "connected": peer.is_connected
                            }
                        }
            
            return {"success": False, "error": "Node not found"}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def handle_create_transaction(self, params: Dict) -> Dict:
        """
        Create a new transaction.
        
        Args:
            params: Request parameters
            
        Returns:
            Response dictionary
        """
        try:
            transaction_data = params.get("data", {})
            
            if hasattr(self.blockchain, "add_transaction"):
                transaction = self.blockchain.add_transaction(
                    transaction_data.get("sender"),
                    transaction_data.get("recipient"),
                    transaction_data.get("amount"),
                    transaction_data.get("fee"),
                    transaction_data.get("data")
                )
                
                return {"success": True, "transaction": transaction.to_dict()}
            
            return {"success": False, "error": "Transaction creation not supported"}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def handle_mine_block(self, params: Dict) -> Dict:
        """
        Mine a new block.
        
        Args:
            params: Request parameters
            
        Returns:
            Response dictionary
        """
        try:
            if hasattr(self.blockchain, "mine_block"):
                block = self.blockchain.mine_block()
                
                return {"success": True, "block": block.to_dict()}
            
            return {"success": False, "error": "Mining not supported"}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def handle_deploy_contract(self, params: Dict) -> Dict:
        """
        Deploy a smart contract.
        
        Args:
            params: Request parameters
            
        Returns:
            Response dictionary
        """
        try:
            contract_data = params.get("data", {})
            
            if hasattr(self.blockchain, "deploy_contract"):
                contract_address = self.blockchain.deploy_contract(
                    contract_data.get("source_code"),
                    contract_data.get("language", "simple"),
                    contract_data.get("compiler_options", {})
                )
                
                return {"success": True, "contract_address": contract_address}
            
            return {"success": False, "error": "Contract deployment not supported"}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def handle_get_contract(self, params: Dict) -> Dict:
        """
        Get contract information.
        
        Args:
            params: Request parameters
            
        Returns:
            Response dictionary
        """
        try:
            address = params.get("address")
            
            if hasattr(self.blockchain, "get_contract_info"):
                contract_info = self.blockchain.get_contract_info(address)
                
                return {"success": True, "contract": contract_info}
            
            return {"success": False, "error": "Contract not found"}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def handle_execute_contract(self, params: Dict) -> Dict:
        """
        Execute a smart contract.
        
        Args:
            params: Request parameters
            
        Returns:
            Response dictionary
        """
        try:
            address = params.get("address")
            execute_data = params.get("data", {})
            
            if hasattr(self.blockchain, "execute_contract"):
                result = self.blockchain.execute_contract(
                    address,
                    execute_data.get("method"),
                    execute_data.get("params")
                )
                
                return {"success": True, "result": result}
            
            return {"success": False, "error": "Contract execution not supported"}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def start(self):
        """Start the API server."""
        self.running = True
        self.thread = threading.Thread(target=self._run)
        self.thread.start()
        self.logger.info(f"API server started on {self.host}:{self.port}")
    
    def _run(self):
        """Internal server loop."""
        import http.server
        import socketserver
        
        class MyHTTPRequestHandler(http.server.BaseHTTPRequestHandler):
            """Custom request handler."""
            
            def _send_response(self, status_code, content):
                """Send HTTP response."""
                import json
                
                self.send_response(status_code)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                
                response_json = json.dumps(content)
                self.wfile.write(response_json.encode("utf-8"))
            
            def do_GET(self):
                """Handle GET requests."""
                try:
                    # Parse URL
                    path_parts = self.path.split('?', 1)
                    path = path_parts[0]
                    
                    # Parse query parameters
                    params = {}
                    if len(path_parts) > 1:
                        import urllib.parse
                        query = urllib.parse.parse_qs(path_parts[1])
                        for key, value in query.items():
                            params[key] = value[0]
                    
                    # Find matching endpoint
                    for endpoint, methods in self.server.api_server.endpoints.items():
                        if "GET" in methods and self._match_path(path, endpoint):
                            # Extract path parameters
                            path_params = self._extract_path_parameters(path, endpoint)
                            params.update(path_params)
                            
                            # Call handler
                            result = methods["GET"](params)
                            self._send_response(200, result)
                            return
                    
                    self._send_response(404, {"success": False, "error": "Endpoint not found"})
                
                except Exception as e:
                    self._send_response(500, {"success": False, "error": str(e)})
            
            def do_POST(self):
                """Handle POST requests."""
                try:
                    # Read request body
                    content_length = int(self.headers.get("Content-Length", 0))
                    body = self.rfile.read(content_length)
                    
                    import json
                    data = json.loads(body.decode("utf-8"))
                    
                    # Parse URL
                    path_parts = self.path.split('?', 1)
                    path = path_parts[0]
                    
                    # Parse query parameters
                    params = {"data": data}
                    if len(path_parts) > 1:
                        import urllib.parse
                        query = urllib.parse.parse_qs(path_parts[1])
                        for key, value in query.items():
                            params[key] = value[0]
                    
                    # Find matching endpoint
                    for endpoint, methods in self.server.api_server.endpoints.items():
                        if "POST" in methods and self._match_path(path, endpoint):
                            # Extract path parameters
                            path_params = self._extract_path_parameters(path, endpoint)
                            params.update(path_params)
                            
                            # Call handler
                            result = methods["POST"](params)
                            self._send_response(200, result)
                            return
                    
                    self._send_response(404, {"success": False, "error": "Endpoint not found"})
                
                except Exception as e:
                    self._send_response(500, {"success": False, "error": str(e)})
            
            def _match_path(self, path, endpoint):
                """Check if path matches endpoint."""
                path = path.rstrip('/')
                endpoint = endpoint.rstrip('/')
                
                if path == endpoint:
                    return True
                
                # Handle placeholders like /blocks/<index>
                path_parts = path.split('/')
                endpoint_parts = endpoint.split('/')
                
                if len(path_parts) != len(endpoint_parts):
                    return False
                
                for p, e in zip(path_parts, endpoint_parts):
                    if e.startswith('<') and e.endswith('>'):
                        continue
                    if p != e:
                        return False
                
                return True
            
            def _extract_path_parameters(self, path, endpoint):
                """Extract path parameters from matched endpoint."""
                params = {}
                path_parts = path.split('/')
                endpoint_parts = endpoint.split('/')
                
                for p, e in zip(path_parts, endpoint_parts):
                    if e.startswith('<') and e.endswith('>'):
                        # Extract parameter name and type
                        param_info = e[1:-1]
                        if ':' in param_info:
                            name, param_type = param_info.split(':')
                        else:
                            name, param_type = param_info, "str"
                        
                        # Convert to appropriate type
                        if param_type == "int":
                            value = int(p)
                        elif param_type == "float":
                            value = float(p)
                        else:
                            value = p
                        
                        params[name] = value
                
                return params
        
        with socketserver.TCPServer((self.host, self.port), MyHTTPRequestHandler) as httpd:
            httpd.api_server = self
            self.server = httpd
            while self.running:
                httpd.handle_request()
    
    def stop(self):
        """Stop the API server."""
        self.running = False
        if self.server:
            self.server.shutdown()
        if self.thread:
            self.thread.join()
        self.logger.info("API server stopped")
    
    def is_running(self):
        """Check if server is running."""
        return self.running
    
    def __repr__(self):
        """String representation of server."""
        return f"ApiServer(host={self.host}, port={self.port}, running={self.running})"
    
    def __str__(self):
        """String representation for printing."""
        status = "Running" if self.running else "Stopped"
        
        return (
            f"ChainForgeLedger API Server\n"
            f"===========================\n"
            f"Host: {self.host}\n"
            f"Port: {self.port}\n"
            f"Status: {status}\n"
            f"Endpoints: {len(self.endpoints)}\n"
            f"Description: Blockchain API Interface"
        )
