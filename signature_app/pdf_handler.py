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
    
    try:
        # Read the PDF and calculate initial hash
        with open(input_path, 'rb') as f:
            pdf_content = f.read()
            initial_hash = hashlib.sha256(pdf_content).digest()
        
        # Read the PDF for processing
        with open(input_path, 'rb') as f:
            try:
                pdf_reader = PdfReader(f)
            except Exception as e:
                print(f"Error reading PDF: {str(e)}")
                raise ValueError("The PDF file appears to be corrupted or invalid. Please try with a different PDF file.")
            
            pdf_writer = PdfWriter()
            
            print(f"Original PDF has {len(pdf_reader.pages)} pages")
            
            # Copy all pages from the original PDF
            for page_num in range(len(pdf_reader.pages)):
                try:
                    page = pdf_reader.pages[page_num]
                    pdf_writer.add_page(page)
                except Exception as e:
                    print(f"Error processing page {page_num + 1}: {str(e)}")
                    raise ValueError(f"Error processing page {page_num + 1}. The PDF may be corrupted.")
            
            # Calculate hash of the PDF content
            pdf_hash = hashlib.sha256()
            print("Calculating document hash for signing...")
            
            # Create a buffer with the PDF content
            pdf_buffer = io.BytesIO()
            pdf_writer.write(pdf_buffer)
            pdf_content_to_hash = pdf_buffer.getvalue()
            
            # Hash the PDF content
            pdf_hash.update(pdf_content_to_hash)
            print(f"PDF content length: {len(pdf_content_to_hash)} bytes")
            
            # Add the initial hash to the content hash
            pdf_hash.update(initial_hash)
            
            print(f"DEBUG: Signing - PDF hash: {pdf_hash.hexdigest()}")
            print(f"Hash bytes length: {len(pdf_hash.digest())} bytes")
            
            # Sign the hash
            print("\nGenerating signature...")
            signature = sign_data(pdf_hash.digest(), private_key_pem)
            print(f"Signature bytes length: {len(signature)} bytes")
            print(f"Signature hex: {signature.hex()[:64]}...")
            
            # Add metadata
            print("\nAdding document metadata...")
            metadata = {
                '/PAdES-Signature': 'True',
                '/SignatureDate': f"{os.path.basename(input_path)}",
                '/SignatureType': 'RSA-SHA256',
                '/Signature': signature.hex(),  # Store signature in metadata
                '/InitialHash': initial_hash.hex(),  # Store initial hash in metadata
                '/Title': pdf_reader.metadata.get('/Title', '') + ' (Digitally Signed)',
                '/Author': pdf_reader.metadata.get('/Author', ''),
                '/Subject': pdf_reader.metadata.get('/Subject', ''),
                '/Keywords': pdf_reader.metadata.get('/Keywords', ''),
                '/Creator': pdf_reader.metadata.get('/Creator', ''),
                '/Producer': pdf_reader.metadata.get('/Producer', ''),
                '/CreationDate': pdf_reader.metadata.get('/CreationDate', ''),
                '/ModDate': pdf_reader.metadata.get('/ModDate', '')
            }
            pdf_writer.add_metadata(metadata)
            print(f"Added metadata keys: {list(metadata.keys())}")
            
            # Save the signed PDF
            print(f"\nSaving signed PDF to {output_path}...")
            try:
                with open(output_path, 'wb') as output_file:
                    pdf_writer.write(output_file)
                print("PDF signed successfully")
            except Exception as e:
                print(f"Error saving signed PDF: {str(e)}")
                raise ValueError("Error saving the signed PDF. Please check if you have write permissions to the output location.")
    except Exception as e:
        print(f"Error during PDF signing process: {str(e)}")
        raise ValueError(f"Failed to sign document: {str(e)}")

def create_signature_page(signature, initial_hash):
    """
    Create a PDF page containing the signature information.
    
    Args:
        signature (bytes): The digital signature
        initial_hash (bytes): Hash of the original PDF content
        
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
    c.drawString(72, height - 140, "Document Hash: " + initial_hash.hex()[:16])
    c.drawString(72, height - 160, "Signature Hash: " + hashlib.sha256(signature).hexdigest()[:16])
    
    # Add signature value visualization (first 64 chars of hex representation)
    c.setFont("Courier", 10)
    c.drawString(72, height - 200, "Signature Value (Visualization):")
    
    # Split signature into multiple lines
    line_length = 64
    print("Adding signature visualization to page text:")
    for i in range(0, min(len(signature.hex()), 256), line_length):
        line_text = signature.hex()[i:i+line_length]
        y_pos = height - 220 - (i // line_length * 15)
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
        pdf_content = f.read()
        pdf_reader = PdfReader(io.BytesIO(pdf_content))
        
        print("\n=== DETAILED SIGNATURE VERIFICATION DEBUGGING ===")
        print(f"PDF File: {pdf_path}")
        
        # Check if this is a signed PDF
        if '/PAdES-Signature' not in pdf_reader.metadata:
            print("ERROR: No PAdES-Signature metadata found!")
            raise ValueError("This PDF does not contain a PAdES signature")
        else:
            print(f"PAdES-Signature metadata found: {pdf_reader.metadata['/PAdES-Signature']}")
        
        # Extract the signature from the metadata
        if '/Signature' not in pdf_reader.metadata:
            print("ERROR: No signature found in metadata!")
            raise ValueError("No signature found in document metadata")
        
        signature_hex = pdf_reader.metadata['/Signature']
        print(f"Found signature in metadata: {signature_hex[:16]}...")
        
        # Get initial hash from metadata
        if '/InitialHash' not in pdf_reader.metadata:
            print("ERROR: No initial hash found in metadata!")
            raise ValueError("No initial hash found in document metadata")
        
        initial_hash_hex = pdf_reader.metadata['/InitialHash']
        print(f"Found initial hash in metadata: {initial_hash_hex[:16]}...")
        initial_hash = bytes.fromhex(initial_hash_hex)
        
        try:
            # Convert hex to bytes
            print("Converting signature from hex to bytes...")
            signature = bytes.fromhex(signature_hex)
            print(f"Signature bytes length: {len(signature)} bytes")
            print(f"Signature first 16 bytes: {signature.hex()[:32]}")
            
            # Now calculate the hash of the content
            print("\nCalculating document hash...")
            pdf_hash = hashlib.sha256()
            
            # Create a new PDF writer to get the content without metadata
            pdf_writer = PdfWriter()
            
            # Copy all pages from the original PDF
            for page in pdf_reader.pages:
                pdf_writer.add_page(page)
            
            # Get the PDF content without metadata
            pdf_buffer = io.BytesIO()
            pdf_writer.write(pdf_buffer)
            pdf_content_to_hash = pdf_buffer.getvalue()
            
            # Hash the PDF content
            pdf_hash.update(pdf_content_to_hash)
            print(f"PDF content length: {len(pdf_content_to_hash)} bytes")
            
            # Add the initial hash to the content hash
            pdf_hash.update(initial_hash)
            print("Added initial hash to content hash")
            
            print(f"Final hash digest: {pdf_hash.hexdigest()}")
            print(f"Hash bytes length: {len(pdf_hash.digest())} bytes")
            
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