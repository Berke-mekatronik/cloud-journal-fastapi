data "aws_ami" "amazon_linux" {
  most_recent = true

  owners = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-*-x86_64"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}


resource "aws_vpc" "journal_vpc_test" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name = "${var.project_name}-vpc-test"
  }
}

resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.journal_vpc_test.id
  cidr_block              = var.public_subnet_cidr
  map_public_ip_on_launch = true

  tags = {
    Name = "${var.project_name}-public-subnet"
  }
}

resource "aws_subnet" "private" {
  vpc_id     = aws_vpc.journal_vpc_test.id
  cidr_block = var.private_subnet_cidr

  tags = {
    Name = "${var.project_name}-private-subnet"
  }
}

resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.journal_vpc_test.id
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.journal_vpc_test.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.igw.id
  }
}

resource "aws_route_table_association" "public" {
  subnet_id      = aws_subnet.public.id
  route_table_id = aws_route_table.public.id
}

resource "aws_security_group" "journal_api_sg" {
  name        = "${var.project_name}-api-sg"
  description = "Security group for FastAPI server"
  vpc_id      = aws_vpc.journal_vpc_test.id

  tags = {
    Name = "${var.project_name}-api-sg"
  }
}

resource "aws_vpc_security_group_ingress_rule" "api_http" {
  security_group_id = aws_security_group.journal_api_sg.id

  cidr_ipv4   = "0.0.0.0/0"
  from_port   = 80
  to_port     = 80
  ip_protocol = "tcp"
}

resource "aws_vpc_security_group_ingress_rule" "api_https" {
  security_group_id = aws_security_group.journal_api_sg.id

  cidr_ipv4   = "0.0.0.0/0"
  from_port   = 443
  to_port     = 443
  ip_protocol = "tcp"
}

resource "aws_vpc_security_group_ingress_rule" "api_ssh" {
  security_group_id = aws_security_group.journal_api_sg.id

  cidr_ipv4   = "${var.my_ip}/32"
  from_port   = 22
  to_port     = 22
  ip_protocol = "tcp"
}

resource "aws_vpc_security_group_egress_rule" "api_all_outbound" {
  security_group_id = aws_security_group.journal_api_sg.id

  cidr_ipv4   = "0.0.0.0/0"
  ip_protocol = "-1"
}

resource "aws_vpc_security_group_egress_rule" "api_to_db_postgres" {
  security_group_id = aws_security_group.journal_api_sg.id

  referenced_security_group_id = aws_security_group.journal_db_sg.id
  from_port                    = 5432
  to_port                      = 5432
  ip_protocol                  = "tcp"
}

resource "aws_security_group" "journal_db_sg" {
  name        = "${var.project_name}-db-sg"
  description = "Security group for PostgreSQL"
  vpc_id      = aws_vpc.journal_vpc_test.id

  tags = {
    Name = "${var.project_name}-db-sg"
  }
}

resource "aws_vpc_security_group_ingress_rule" "db_postgres" {
  security_group_id = aws_security_group.journal_db_sg.id

  referenced_security_group_id = aws_security_group.journal_api_sg.id
  from_port                    = 5432
  to_port                      = 5432
  ip_protocol                  = "tcp"
}

resource "aws_vpc_security_group_egress_rule" "db_all_outbound" {
  security_group_id = aws_security_group.journal_db_sg.id

  cidr_ipv4   = "0.0.0.0/0"
  ip_protocol = "-1"
}

resource "aws_instance" "journal_fastapi_test" {
  ami                    = data.aws_ami.amazon_linux.id
  instance_type          = "t2.micro"
  subnet_id              = aws_subnet.public.id
  vpc_security_group_ids = [aws_security_group.journal_api_sg.id]

  tags = {
    Name = "${var.project_name}-fastapi-test"
  }
}

resource "aws_instance" "journal_database_test" {
  ami                    = data.aws_ami.amazon_linux.id
  instance_type          = "t2.micro"
  subnet_id              = aws_subnet.private.id
  vpc_security_group_ids = [aws_security_group.journal_db_sg.id]

  tags = {
    Name = "${var.project_name}-database-test"
  }
}

