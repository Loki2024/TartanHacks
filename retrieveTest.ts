import axios from 'axios';
import { config as dotenvConfig } from 'dotenv';

// Load environment variables
dotenvConfig();

const PINATA_JWT = process.env.PINATA_JWT;

console.log('JWT Token loaded:', PINATA_JWT ? 'Present' : 'Missing');

async function getAllPinataCIDs() {
    try {
        const response = await axios.get('https://api.pinata.cloud/data/pinList', {
            headers: {
                'Authorization': Bearer ${PINATA_JWT}
            }
        });

        console.log('Your Pinata CIDs:');
        response.data.rows.forEach((pin: any) => {
            console.log(CID: ${pin.ipfs_pin_hash});
            console.log(Name: ${pin.metadata.name});
            console.log('------------------------');
        });

    } catch (error) {
        console.error('Error fetching Pinata pins:', error);
    }
}

// Execute the function
getAllPinataCIDs().catch(console.error);