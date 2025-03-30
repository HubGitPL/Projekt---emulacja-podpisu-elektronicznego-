"""
PDF handling module for signing and verifying PDF documents.
"""
import io
import hashlib
import os
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from crypto import sign_data, verify_signature

def sign_pdf(input_path, output_path, private_key_pem):
    """
    Sign a PDF document and embed the signature.
    
    Args:
        input_path (str): Path to the input PDF
        output_path (str): Path to save the signed PDF
        private_key_pem (bytes): PEM-encoded private key
    """
    print("\n=== DETAILED PDF SIGNING DEBUGGING ===")
    print(f"Input PDF: {input_path}")
    print(f"Output PDF: {output_path}")
    
    # Read the PDF
    with open(input_path, 'rb') as f:
        pdf_reader = PdfReader(f)
        pdf_writer = PdfWriter()
        
        print(f"Original PDF has {len(pdf_reader.pages)} pages")
        
        # Copy all pages from the original PDF
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            pdf_writer.add_page(page)
        
        # Calculate hash of the PDF content
        # This needs to match how it's calculated during verification
        pdf_hash = hashlib.sha256()
        print("Calculating document hash for signing...")
        for page_num in range(len(pdf_reader.pages)):
            page_content = pdf_reader.pages[page_num].extract_text().encode('utf-8')
            print(f"  Page {page_num+1} content length: {len(page_content)} bytes")
            pdf_hash.update(page_content)
        
        print(f"DEBUG: Signing - PDF hash: {pdf_hash.hexdigest()}")
        print(f"Hash bytes length: {len(pdf_hash.digest())} bytes")
        
        # Sign the hash
        print("\nGenerating signature...")
        signature = sign_data(pdf_hash.digest(), private_key_pem)
        print(f"Signature bytes length: {len(signature)} bytes")
        print(f"Signature hex: {signature.hex()[:64]}...")
        
        # Create a signature page
        print("\nCreating signature page...")
        signature_page = create_signature_page(signature)
        
        # Add signature page to the PDF
        signature_reader = PdfReader(signature_page)
        signature_page = signature_reader.pages[0]
        pdf_writer.add_page(signature_page)
        print(f"Added signature page, total pages now: {len(pdf_writer.pages)}")
        
        # Add metadata
        print("\nAdding document metadata...")
        metadata = {
            '/PAdES-Signature': 'True',
            '/SignatureDate': f"{os.path.basename(input_path)}",
            '/SignatureType': 'RSA-SHA256',
            '/Author': f"SIGNATURE:{signature.hex()}"  # Store signature in document metadata as well
        }
        pdf_writer.add_metadata(metadata)
        print(f"Added metadata keys: {list(metadata.keys())}")
        
        # Save the signed PDF
        print(f"\nSaving signed PDF to {output_path}...")
        with open(output_path, 'wb') as output_file:
            pdf_writer.write(output_file)
        print("PDF signed successfully")

def create_signature_page(signature):
    """
    Create a PDF page containing the signature information.
    
    Args:
        signature (bytes): The digital signature
        
    Returns:
        io.BytesIO: PDF page as a bytes buffer
    """
    print("Creating signature page with signature details...")
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Add title
    c.setFont("Helvetica-Bold", 16)
    c.drawString(72, height - 72, "Digital Signature")
    
    # Add signature information
    c.setFont("Helvetica", 12)
    c.drawString(72, height - 100, "This document has been digitally signed.")
    c.drawString(72, height - 120, "Signature Algorithm: RSA-SHA256")
    c.drawString(72, height - 140, "Signature Hash: " + 
                 hashlib.sha256(signature).hexdigest()[:16])
    
    # Store raw signature as metadata in the PDF
    signature_hex = signature.hex()
    print(f"Setting Author metadata with signature (length: {len(signature_hex)} chars)")
    c.setAuthor("SIGNATURE:" + signature_hex)
    
    # Add signature value visualization (first 64 chars of hex representation)
    c.setFont("Courier", 10)
    c.drawString(72, height - 180, "Signature Value (Visualization):")
    
    # Split signature into multiple lines
    line_length = 64
    print("Adding signature visualization to page text:")
    for i in range(0, min(len(signature_hex), 256), line_length):
        line_text = signature_hex[i:i+line_length]
        y_pos = height - 200 - (i // line_length * 15)
        c.drawString(72, y_pos, line_text)
        print(f"  Line at y={y_pos}: {line_text[:16]}...")
    
    c.save()
    buffer.seek(0)
    return buffer

def verify_pdf_signature(pdf_path, public_key_pem):
    """
    Verify the signature of a signed PDF document.
    
    Args:
        pdf_path (str): Path to the signed PDF
        public_key_pem (bytes): PEM-encoded public key
        
    Returns:
        bool: True if signature is valid, False otherwise
    """
    with open(pdf_path, 'rb') as f:
        pdf_reader = PdfReader(f)
        
        print("\n=== DETAILED SIGNATURE VERIFICATION DEBUGGING ===")
        print(f"PDF File: {pdf_path}")
        
        # Check if this is a signed PDF
        if '/PAdES-Signature' not in pdf_reader.metadata:
            print("ERROR: No PAdES-Signature metadata found!")
            raise ValueError("This PDF does not contain a PAdES signature")
        else:
            print(f"PAdES-Signature metadata found: {pdf_reader.metadata['/PAdES-Signature']}")
        
        # Extract the signature from the metadata of the last page
        if len(pdf_reader.pages) < 2:
            raise ValueError("Invalid signed PDF format")
        
        print(f"Total pages in PDF: {len(pdf_reader.pages)}")
        
        # Get the signature first
        signature_hex = None
        print("\nLooking for signature in various locations:")
        
        # 1. Check page Author metadata
        print("1. Checking last page Resources/Author metadata...")
        if '/Author' in pdf_reader.pages[-1].get('/Resources', {}):
            author_info = pdf_reader.pages[-1].get('/Resources', {}).get('/Author', '')
            print(f"  Found Author in page resources: {author_info[:30]}...")
            if 'SIGNATURE:' in author_info:
                signature_hex = author_info.split('SIGNATURE:')[1].strip()
                print(f"  Found signature in page Author metadata: {signature_hex[:16]}...")
        else:
            print("  No Author in page resources found")

        # 2. Check document metadata
        print("2. Checking document metadata...")
        if not signature_hex:
            # Using metadata instead of deprecated getDocumentInfo
            metadata = pdf_reader.metadata
            print(f"  Available metadata keys: {list(metadata.keys() if metadata else [])}")
            if metadata and '/Author' in metadata:
                print(f"  Author metadata: {metadata['/Author'][:30]}...")
                if 'SIGNATURE:' in metadata['/Author']:
                    signature_hex = metadata['/Author'].split('SIGNATURE:')[1].strip()
                    print(f"  Found signature in document metadata: {signature_hex[:16]}...")
                else:
                    print("  No SIGNATURE: marker found in Author metadata")
            else:
                print("  No Author metadata found")
            
        # 3. Extract from text as fallback
        print("3. Checking signature page text...")
        if not signature_hex:
            # Debug print to see the actual metadata
            print(f"  Full PDF Metadata: {pdf_reader.metadata}")
            
            signature_page_text = pdf_reader.pages[-1].extract_text()
            print(f"  Signature page text length: {len(signature_page_text)} bytes")
            
            # Find the signature value in the text
            signature_start = signature_page_text.find("Signature Value")
            if signature_start == -1:
                print("  No 'Signature Value' text found in the last page")
                raise ValueError("Signature value not found in the document")
            else:
                print(f"  Found 'Signature Value' at position {signature_start}")
            
            # Extract the signature hex string
            lines = signature_page_text[signature_start:].split('\n')
            signature_hex = ''
            capturing = False
            print("  Extracting signature from text lines:")
            for line in lines:
                if "Signature Value" in line:
                    capturing = True
                    print(f"    Start capturing from: {line}")
                    continue
                if capturing and line.strip() and all(c.isalnum() for c in line.strip()):
                    signature_hex += line.strip()
                    print(f"    Found hex content: {line.strip()[:16]}... (length: {len(line.strip())})")
                # Stop when we hit non-hex content
                elif capturing and line.strip() and not all(c.isalnum() for c in line.strip()):
                    print(f"    Stopped at non-hex line: {line.strip()[:30]}...")
                    break
        
        if not signature_hex:
            print("ERROR: Could not extract signature from document!")
            raise ValueError("Could not extract signature from the document")
            
        print(f"\nExtracted signature hex length: {len(signature_hex)} characters")
        
        try:
            # Convert hex to bytes
            print("Converting signature from hex to bytes...")
            signature = bytes.fromhex(signature_hex)
            print(f"Signature bytes length: {len(signature)} bytes")
            print(f"Signature first 16 bytes: {signature.hex()[:32]}")
            
            # Now calculate the hash of the content
            # IMPORTANT: This must exactly match how it's calculated during signing
            # Calculate hash of the PDF content (excluding signature page)
            print("\nCalculating document hash (excluding signature page)...")
            pdf_hash = hashlib.sha256()
            
            # During signing, we hash ALL pages of the ORIGINAL document.
            # Here we need to hash all pages EXCEPT the signature page that was added.
            total_pages = len(pdf_reader.pages)
            for page_num in range(total_pages - 1):  # Skip the last page (signature page)
                print(f"  Processing page {page_num+1}/{total_pages-1}...")
                page_content = pdf_reader.pages[page_num].extract_text().encode('utf-8')
                print(f"  Page {page_num+1} content length: {len(page_content)} bytes")
                # Show the first few bytes of each page for debugging
                if len(page_content) > 0:
                    print(f"  First few bytes: {page_content[:20]}")
                pdf_hash.update(page_content)
                
            print(f"Final hash digest: {pdf_hash.hexdigest()}")
            print(f"Hash bytes length: {len(pdf_hash.digest())} bytes")
            
            # Check the public key
            print("\nVerifying with public key...")
            from cryptography.hazmat.primitives import serialization
            try:
                public_key = serialization.load_pem_public_key(public_key_pem)
                print("Public key loaded successfully")
            except Exception as e:
                print(f"ERROR loading public key: {str(e)}")
                
            # Verify the signature
            print("\nAttempting signature verification...")
            print(f"Data hash to verify: {pdf_hash.hexdigest()}")
            print(f"Data hash bytes length: {len(pdf_hash.digest())} bytes")
            
            result = verify_signature(pdf_hash.digest(), signature, public_key_pem)
            print(f"DEBUG: Verification result: {result}")
            return result
        except Exception as e:
            print(f"DEBUG: Verification exception: {str(e)}")
            raise ValueError(f"Failed to verify signature: {str(e)}") 