import React, { useState } from 'react';
import './QuizDisplay.css';
import { useAuth } from '../AuthContext';

const QuizDisplay = ({ questions, onWrongAnswer, onCreateRevision }) => {
    const { userId } = useAuth();
    // Track selected option for each question: { [questionIndex]: selectedOptionString }
    const [selectedOptions, setSelectedOptions] = useState({});
    // Track checked state to disable further clicks: { [questionIndex]: boolean }
    const [checkedState, setCheckedState] = useState({});
    const [isFeedbackOpen, setIsFeedbackOpen] = useState(false);
    const [feedbackText, setFeedbackText] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [feedbackStatus, setFeedbackStatus] = useState(null); // { type: 'success' | 'error', message: string }

    const handleOptionClick = (questionIndex, option, correctOption, questionObj) => {
        // If already checked, do nothing
        if (checkedState[questionIndex]) return;

        setSelectedOptions(prev => ({
            ...prev,
            [questionIndex]: option
        }));

        setCheckedState(prev => ({
            ...prev,
            [questionIndex]: true
        }));

        // Check correctness
        if (option !== correctOption) {
            if (onWrongAnswer) {
                onWrongAnswer(questionObj);
            }
        }
    };

    const handleFeedbackSubmit = async () => {
        if (!feedbackText.trim()) return;

        setIsSubmitting(true);
        setFeedbackStatus(null);
        try {
            const result = await submitFeedback(userId, feedbackText);
            setFeedbackStatus({
                type: 'success',
                message: result.stored ? 'Preference saved!' : 'Feedback received.'
            });
            setFeedbackText('');
            // Auto-close after 2 seconds
            setTimeout(() => {
                setIsFeedbackOpen(false);
                setFeedbackStatus(null);
            }, 2000);
        } catch (error) {
            setFeedbackStatus({ type: 'error', message: 'Failed to send feedback.' });
        } finally {
            setIsSubmitting(false);
        }
    };

    const getOptionClass = (questionIndex, option, correctOption) => {
        if (!checkedState[questionIndex]) {
            return 'quiz-option'; // Normal state
        }

        if (option === correctOption) {
            return 'quiz-option correct'; // Always show correct option in green
        }

        if (selectedOptions[questionIndex] === option) {
            return 'quiz-option wrong'; // Show selected wrong option in red
        }

        return 'quiz-option disabled'; // Other options
    };

    if (!Array.isArray(questions) || questions.length === 0) {
        console.warn('QuizDisplay received invalid questions:', questions);
        return <div className="quiz-empty">No quiz questions available.</div>;
    }

    return (
        <div className="quiz-display">
            <h3>📝 Interactive Quiz</h3>
            <div className="quiz-list">
                {questions.map((q, qIndex) => (
                    <div key={qIndex} className="quiz-card">
                        <div className="quiz-question-header">
                            <span className="question-number">{qIndex + 1}.</span>
                            <p className="question-text">{q.question}</p>
                        </div>
                        <div className="quiz-options">
                            {q.options.map((option, oIndex) => (
                                <div
                                    key={oIndex}
                                    className={getOptionClass(qIndex, option, q.correct_option)}
                                    onClick={() => handleOptionClick(qIndex, option, q.correct_option, q)}
                                >
                                    <span className="option-marker">{String.fromCharCode(65 + oIndex)}.</span>
                                    <span className="option-text">{option}</span>
                                    {checkedState[qIndex] && option === q.correct_option && (
                                        <span className="result-icon">✓</span>
                                    )}
                                    {checkedState[qIndex] && selectedOptions[qIndex] === option && option !== q.correct_option && (
                                        <span className="result-icon">✕</span>
                                    )}
                                </div>
                            ))}
                        </div>
                        {checkedState[qIndex] && (
                            <div className="timestamp-hint">
                                Related segment: {q.timestamp}
                            </div>
                        )}
                    </div>
                ))}
            </div>

            <div className="quiz-footer" style={{ gap: '15px' }}>
                {onCreateRevision && (
                    <button className="revision-btn" onClick={onCreateRevision}>
                        📝 Create Revision Doc
                    </button>
                )}
                <button className="feedback-toggle-btn" onClick={() => setIsFeedbackOpen(true)}>
                    💬 Provide Feedback
                </button>
            </div>

            {isFeedbackOpen && (
                <div className="feedback-modal-overlay">
                    <div className="feedback-modal">
                        <div className="feedback-modal-header">
                            <h4>Personalize Your Agent</h4>
                            <button className="close-modal" onClick={() => setIsFeedbackOpen(false)}>✕</button>
                        </div>
                        <p className="feedback-hint">
                            Tell the agent how to improve (e.g., "The explanation was too complex" or "I prefer visual examples").
                        </p>
                        <textarea
                            className="feedback-input"
                            placeholder="Type your feedback here..."
                            value={feedbackText}
                            onChange={(e) => setFeedbackText(e.target.value)}
                            disabled={isSubmitting}
                        />
                        {feedbackStatus && (
                            <div className={`feedback-status ${feedbackStatus.type}`}>
                                {feedbackStatus.message}
                            </div>
                        )}
                        <div className="feedback-modal-footer">
                            <button
                                className="submit-feedback-btn"
                                onClick={handleFeedbackSubmit}
                                disabled={isSubmitting || !feedbackText.trim()}
                            >
                                {isSubmitting ? 'Sending...' : 'Submit Feedback'}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default QuizDisplay;
