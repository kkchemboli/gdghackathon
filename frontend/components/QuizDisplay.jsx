import React, { useState } from 'react';
import './QuizDisplay.css';

const QuizDisplay = ({ questions, onWrongAnswer, onCreateRevision }) => {
    // Track selected option for each question: { [questionIndex]: selectedOptionString }
    const [selectedOptions, setSelectedOptions] = useState({});
    // Track checked state to disable further clicks: { [questionIndex]: boolean }
    const [checkedState, setCheckedState] = useState({});

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

            {onCreateRevision && (
                <div className="quiz-footer">
                    <button className="revision-btn" onClick={onCreateRevision}>
                        📝 Create Revision Doc
                    </button>
                </div>
            )}
        </div>
    );
};

export default QuizDisplay;
