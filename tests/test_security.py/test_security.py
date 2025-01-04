import pytest
from datetime import datetime, timedelta
from agoraai.security.authentication import (
    AuthenticationManager,
    AgentCredentials,
    SessionManager
)
from agoraai.security.encryption import (
    EncryptionManager,
    SecureChannel,
    DataEncryption
)
from agoraai.security.permissions import (
    Permission,
    Role,
    PermissionManager,
    AccessControl
)

@pytest.fixture
def auth_manager():
    return AuthenticationManager("test_secret_key")

@pytest.fixture
def encryption_manager():
    return EncryptionManager()

@pytest.fixture
def permission_manager():
    return PermissionManager()

class TestAuthentication:
    def test_agent_registration(self, auth_manager):
        credentials = auth_manager.register_agent("agent1")
        assert isinstance(credentials, AgentCredentials)
        assert credentials.agent_id == "agent1"
        assert credentials.private_key is not None
        assert credentials.public_key is not None
        
    def test_agent_authentication(self, auth_manager):
        credentials = auth_manager.register_agent("agent1")
        token = auth_manager.authenticate_agent(
            "agent1",
            credentials.private_key
        )
        assert token is not None
        
        # Test invalid authentication
        invalid_token = auth_manager.authenticate_agent(
            "agent1",
            "invalid_key"
        )
        assert invalid_token is None
        
    def test_token_validation(self, auth_manager):
        credentials = auth_manager.register_agent("agent1")
        token = auth_manager.authenticate_agent(
            "agent1",
            credentials.private_key
        )
        
        agent_id = auth_manager.validate_token(token)
        assert agent_id == "agent1"
        
        # Test invalid token
        invalid_agent = auth_manager.validate_token("invalid_token")
        assert invalid_agent is None
        
    def test_token_revocation(self, auth_manager):
        credentials = auth_manager.register_agent("agent1")
        token = auth_manager.authenticate_agent(
            "agent1",
            credentials.private_key
        )
        
        auth_manager.revoke_token(token)
        assert auth_manager.validate_token(token) is None

class TestSession:
    @pytest.fixture
    def session_manager(self, auth_manager):
        return SessionManager(auth_manager)
    
    def test_session_creation(self, session_manager, auth_manager):
        credentials = auth_manager.register_agent("agent1")
        session_id = session_manager.create_session("agent1")
        assert session_id is not None
        
    def test_session_validation(self, session_manager, auth_manager):
        credentials = auth_manager.register_agent("agent1")
        session_id = session_manager.create_session("agent1")
        
        assert session_manager.validate_session(session_id) is True
        assert session_manager.validate_session("invalid_session") is False
        
    def test_session_expiry(self, session_manager, auth_manager):
        credentials = auth_manager.register_agent("agent1")
        session_id = session_manager.create_session("agent1")
        
        # Simulate session timeout
        session = session_manager.active_sessions[session_id]
        session["last_accessed"] = datetime.now() - timedelta(hours=2)
        
        assert session_manager.validate_session(session_id) is False
        
    def test_session_data(self, session_manager, auth_manager):
        credentials = auth_manager.register_agent("agent1")
        session_id = session_manager.create_session("agent1")
        
        # Update session metadata
        session_manager.update_session_metadata(
            session_id,
            {"last_action": "test"}
        )
        
        session_data = session_manager.get_session_data(session_id)
        assert session_data is not None
        assert session_data["metadata"]["last_action"] == "test"

class TestEncryption:
    def test_key_generation(self, encryption_manager):
        private_key, public_key = encryption_manager.generate_key_pair()
        assert private_key is not None
        assert public_key is not None
        
    def test_message_encryption(self, encryption_manager):
        private_key, public_key = encryption_manager.generate_key_pair()
        message = b"test message"
        
        encrypted = encryption_manager.encrypt_message(message, public_key)
        decrypted = encryption_manager.decrypt_message(encrypted, private_key)
        
        assert decrypted == message
        
    def test_symmetric_encryption(self, encryption_manager):
        data = b"test data"
        encrypted = encryption_manager.symmetric_encrypt(data)
        decrypted = encryption_manager.symmetric_decrypt(encrypted)
        
        assert decrypted == data
        
    def test_secure_channel(self, encryption_manager):
        channel = SecureChannel(encryption_manager)
        connection_data = channel.initialize()
        
        assert "public_key" in connection_data
        assert "session_key" in connection_data

class TestDataEncryption:
    def test_file_encryption(self, tmp_path, encryption_manager):
        data_encryption = DataEncryption(encryption_manager)
        test_file = tmp_path / "test.txt"
        
        # Create test file
        with open(test_file, 'wb') as f:
            f.write(b"test content")
        
        # Encrypt file
        encrypted_data, key = data_encryption.encrypt_file(str(test_file))
        assert encrypted_data != b"test content"
        
        # Decrypt file
        decrypted_data = data_encryption.decrypt_file(encrypted_data, key)
        assert decrypted_data == b"test content"
        
    def test_key_storage(self, encryption_manager):
        data_encryption = DataEncryption(encryption_manager)
        key = b"test_key"
        
        data_encryption.store_key("key1", key)
        retrieved_key = data_encryption.retrieve_key("key1")
        
        assert retrieved_key == key
        
        data_encryption.remove_key("key1")
        assert data_encryption.retrieve_key("key1") is None

class TestPermissions:
    def test_role_creation(self, permission_manager):
        role = permission_manager.create_role(
            "admin",
            {Permission.READ, Permission.WRITE, Permission.ADMIN},
            "Administrator role"
        )
        assert role.name == "admin"
        assert Permission.ADMIN in role.permissions
        
    def test_role_assignment(self, permission_manager):
        permission_manager.create_role(
            "user",
            {Permission.READ, Permission.WRITE}
        )
        permission_manager.assign_role("agent1", "user")
        
        roles = permission_manager.get_user_roles("agent1")
        assert "user" in roles
        
    def test_permission_checking(self, permission_manager):
        permission_manager.create_role(
            "user",
            {Permission.READ}
        )
        permission_manager.assign_role("agent1", "user")
        
        assert permission_manager.has_permission("agent1", Permission.READ)
        assert not permission_manager.has_permission("agent1", Permission.ADMIN)
        
    def test_resource_access_control(self, permission_manager):
        permission_manager.create_access_control(
            "resource1",
            "owner1"
        )
        
        permission_manager.grant_permission(
            "agent1",
            Permission.READ,
            "resource1"
        )
        
        assert permission_manager.has_permission(
            "agent1",
            Permission.READ,
            "resource1"
        )
        
        permission_manager.revoke_permission(
            "agent1",
            Permission.READ,
            "resource1"
        )
        
        assert not permission_manager.has_permission(
            "agent1",
            Permission.READ,
            "resource1"
        )