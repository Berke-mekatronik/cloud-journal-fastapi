output "api_public_ip" {
  value = aws_instance.journal_fastapi_test.public_ip
}

