import { config } from 'dotenv';
import { resolve } from 'path';
import { fileURLToPath } from 'url';
import { dirname } from 'path';

import { TronWeb } from 'tronweb';

import { X402Client } from '@x402/core';
import { X402FetchClient } from '@x402/http-fetch';
import { UptoTronClientMechanism } from '@x402/mechanism-tron';
import { TronClientSigner } from '@x402/signer-tron';
import type { SettleResponse } from '@x402/core';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

config({ path: resolve(__dirname, '../../../../.env') });

const TRON_PRIVATE_KEY = process.env.TRON_PRIVATE_KEY || '';
const TRON_NETWORK = 'tron:nile';
const RESOURCE_SERVER_URL = 'http://localhost:8000';
const ENDPOINT_PATH = '/protected';
const RESOURCE_URL = RESOURCE_SERVER_URL + ENDPOINT_PATH;

if (!TRON_PRIVATE_KEY) {
  console.error('\n❌ Error: TRON_PRIVATE_KEY not set in .env file');
  console.error('\nPlease add your TRON private key to .env file\n');
  process.exit(1);
}

function getTronFullHost(network: string): string {
  const networkName = network.split(':').pop() || 'nile';
  switch (networkName) {
    case 'mainnet':
      return 'https://api.trongrid.io';
    case 'shasta':
      return 'https://api.shasta.trongrid.io';
    case 'nile':
      return 'https://nile.trongrid.io';
    default:
      throw new Error(`Unsupported network: ${network}`);
  }
}

function decodePaymentResponse(encoded: string): SettleResponse | null {
  try {
    const jsonString = Buffer.from(encoded, 'base64').toString('utf8');
    return JSON.parse(jsonString) as SettleResponse;
  } catch {
    return null;
  }
}

async function main(): Promise<void> {
  const networkName = TRON_NETWORK.split(':').pop() || 'nile';
  
  console.log('Initializing X402 client...');
  console.log(`  Network: ${TRON_NETWORK}`);
  console.log(`  Resource: ${RESOURCE_URL}`);

  const tronWeb = new TronWeb({
    fullHost: getTronFullHost(TRON_NETWORK),
  });

  const signer = TronClientSigner.withPrivateKey(
    tronWeb as unknown as never,
    TRON_PRIVATE_KEY,
    networkName as 'mainnet' | 'nile' | 'shasta'
  );
  
  console.log(`  Client Address: ${signer.getAddress()}`);

  const x402Client = new X402Client().register(
    'tron:*',
    new UptoTronClientMechanism(signer)
  );

  const client = new X402FetchClient(x402Client);

  console.log(`\nRequesting: ${RESOURCE_URL}`);
  
  try {
    const response = await client.get(RESOURCE_URL);
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status} ${response.statusText}`);
    }

    console.log('\n✅ Success!');
    console.log(`Status: ${response.status}`);
    console.log(`Content-Type: ${response.headers.get('content-type')}`);
    
    const contentLength = response.headers.get('content-length');
    if (contentLength) {
      console.log(`Content-Length: ${contentLength} bytes`);
    } else {
      const body = await response.arrayBuffer();
      console.log(`Content-Length: ${body.byteLength} bytes`);
    }

    const paymentResponse = response.headers.get('payment-response');
    if (paymentResponse) {
      const settleResponse = decodePaymentResponse(paymentResponse);
      if (settleResponse) {
        console.log('\n📋 Payment Response:');
        console.log(`  Success: ${settleResponse.success}`);
        console.log(`  Network: ${settleResponse.network}`);
        console.log(`  Transaction: ${settleResponse.transaction}`);
        if (settleResponse.errorReason) {
          console.log(`  Error: ${settleResponse.errorReason}`);
        }
      }
    }

    const contentType = response.headers.get('content-type') || '';
    if (contentType.includes('application/json')) {
      const json = await response.json();
      console.log(`\nResponse: ${JSON.stringify(json, null, 2)}`);
    } else if (contentType.includes('image/')) {
      console.log('\n🖼️  Received image file');
    } else {
      const text = await response.text();
      console.log(`\nResponse (first 200 chars): ${text.slice(0, 200)}`);
    }
  } catch (error) {
    console.error('\n❌ Error:', error instanceof Error ? error.message : error);
    if (error instanceof Error && error.stack) {
      console.error(error.stack);
    }
    process.exit(1);
  }
}

main().catch(error => {
  console.error('Fatal error:', error);
  process.exit(1);
});
