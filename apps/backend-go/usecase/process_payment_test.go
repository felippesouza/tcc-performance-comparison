package usecase

import (
	"context"
	"errors"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/mock"
	"github.com/tcc/backend-go/domain"
)

// MockPaymentRepository é um mock para domain.PaymentRepository
type MockPaymentRepository struct {
	mock.Mock
}

func (m *MockPaymentRepository) Save(ctx context.Context, payment domain.Payment) (domain.Payment, error) {
	args := m.Called(ctx, payment)
	return args.Get(0).(domain.Payment), args.Error(1)
}

func (m *MockPaymentRepository) FindByID(ctx context.Context, id string) (*domain.Payment, error) {
	args := m.Called(ctx, id)
	if args.Get(0) != nil {
		return args.Get(0).(*domain.Payment), args.Error(1)
	}
	return nil, args.Error(1)
}

// MockExternalGateway é um mock para domain.ExternalGateway
type MockExternalGateway struct {
	mock.Mock
}

func (m *MockExternalGateway) Process(ctx context.Context, payment domain.Payment) (domain.PaymentResponse, error) {
	args := m.Called(ctx, payment)
	return args.Get(0).(domain.PaymentResponse), args.Error(1)
}

func TestProcessPaymentWithSuccess(t *testing.T) {
	// Arrange
	mockRepo := new(MockPaymentRepository)
	mockGateway := new(MockExternalGateway)
	interactor := NewProcessPaymentInteractor(mockRepo, mockGateway)

	request := domain.Payment{
		Amount:     100.00,
		CardNumber: "1234-5678",
	}

	pendingPayment := domain.Payment{ID: "uuid-123", Amount: 100.00, CardNumber: "1234-5678", Status: "PENDING"}
	extID := "ext_123"
	approvedPayment := domain.Payment{ID: "uuid-123", Amount: 100.00, CardNumber: "1234-5678", Status: "APPROVED", ExternalID: &extID}

	mockRepo.On("Save", mock.Anything, mock.MatchedBy(func(p domain.Payment) bool {
		return p.Status == "PENDING"
	})).Return(pendingPayment, nil).Once()

	mockGateway.On("Process", mock.Anything, mock.Anything).Return(domain.PaymentResponse{
		ExternalID: "ext_123",
		Approved:   true,
	}, nil).Once()

	mockRepo.On("Save", mock.Anything, mock.MatchedBy(func(p domain.Payment) bool {
		return p.Status == "APPROVED" && *p.ExternalID == "ext_123"
	})).Return(approvedPayment, nil).Once()

	// Act
	result, err := interactor.Execute(context.Background(), request)

	// Assert
	assert.NoError(t, err)
	assert.NotNil(t, result)
	assert.Equal(t, "APPROVED", result.Status)
	assert.Equal(t, "ext_123", *result.ExternalID)

	mockRepo.AssertExpectations(t)
	mockGateway.AssertExpectations(t)
}

func TestProcessPayment_ThrowErrorWhenInitialSaveFails(t *testing.T) {
	// Arrange
	mockRepo := new(MockPaymentRepository)
	mockGateway := new(MockExternalGateway)
	interactor := NewProcessPaymentInteractor(mockRepo, mockGateway)

	request := domain.Payment{
		Amount:     100.00,
		CardNumber: "1234-5678",
	}

	mockRepo.On("Save", mock.Anything, mock.Anything).Return(domain.Payment{}, errors.New("database error")).Once()

	// Act
	result, err := interactor.Execute(context.Background(), request)

	// Assert
	assert.Error(t, err)
	assert.Nil(t, result)
	assert.Contains(t, err.Error(), "database error")

	mockGateway.AssertNotCalled(t, "Process")
	mockRepo.AssertExpectations(t)
}

func TestProcessPayment_ThrowErrorWhenGatewayFails(t *testing.T) {
	// Arrange
	mockRepo := new(MockPaymentRepository)
	mockGateway := new(MockExternalGateway)
	interactor := NewProcessPaymentInteractor(mockRepo, mockGateway)

	request := domain.Payment{
		Amount:     100.00,
		CardNumber: "1234-5678",
	}

	pendingPayment := domain.Payment{ID: "uuid-123", Amount: 100.00, CardNumber: "1234-5678", Status: "PENDING"}

	mockRepo.On("Save", mock.Anything, mock.MatchedBy(func(p domain.Payment) bool {
		return p.Status == "PENDING"
	})).Return(pendingPayment, nil).Once()

	mockGateway.On("Process", mock.Anything, mock.Anything).Return(domain.PaymentResponse{}, errors.New("gateway timeout")).Once()

	// Act
	result, err := interactor.Execute(context.Background(), request)

	// Assert
	assert.Error(t, err)
	assert.Nil(t, result)
	assert.Contains(t, err.Error(), "gateway timeout")

	mockRepo.AssertNumberOfCalls(t, "Save", 1)
	
	mockRepo.AssertExpectations(t)
	mockGateway.AssertExpectations(t)
}
