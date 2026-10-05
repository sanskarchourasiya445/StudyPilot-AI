import React, { useState, useEffect } from 'react';
import {
  HelpCircle,
  Sparkles,
  CheckCircle2,
  XCircle,
  ArrowRight,
  ArrowLeft,
  RotateCcw,
  Award,
} from 'lucide-react';
import { Card } from '../ui/Card';
import { Button } from '../ui/Button';
import { Badge } from '../ui/Badge';
import { Skeleton } from '../ui/Skeleton';

import { useSubmitQuizResult } from '../../hooks/useMastery';

export function QuizTab({
  selectedResource,
  quizzes = [],
  isLoadingQuizzes,
  isGenerating,
  onGenerateQuiz,
}) {
  const [difficulty, setDifficulty] = useState('medium');
  const [questionCount, setQuestionCount] = useState(5);

  const [currentQuiz, setCurrentQuiz] = useState(null);
  const [currentQuestionIdx, setCurrentQuestionIdx] = useState(0);
  const [userAnswers, setUserAnswers] = useState({});
  const [submittedQuestions, setSubmittedQuestions] = useState({});
  const [quizCompleted, setQuizCompleted] = useState(false);
  const [masteryResult, setMasteryResult] = useState(null);

  const submitQuizMutation = useSubmitQuizResult();

  useEffect(() => {
    if (quizzes.length > 0) {
      setCurrentQuiz(quizzes[0]);
    } else {
      setCurrentQuiz(null);
    }
  }, [quizzes]);

  const handleFinishQuiz = async () => {
    setQuizCompleted(true);
    if (currentQuiz && questions.length > 0) {
      try {
        const result = await submitQuizMutation.mutateAsync({
          quizId: currentQuiz.id,
          score: correctCount,
          totalQuestions: questions.length,
        });
        setMasteryResult(result);
      } catch (err) {
        console.error("Failed to record quiz attempt:", err);
      }
    }
  };

  const handleGenerate = async () => {
    const newQuiz = await onGenerateQuiz({
      questionCount: parseInt(questionCount, 10),
      difficulty,
    });
    if (newQuiz) {
      setCurrentQuiz(newQuiz);
    }
    setUserAnswers({});
    setSubmittedQuestions({});
    setQuizCompleted(false);
    setCurrentQuestionIdx(0);
  };

  const handleSelectOption = (optionIdx) => {
    if (submittedQuestions[currentQuestionIdx]) return;
    setUserAnswers((prev) => ({
      ...prev,
      [currentQuestionIdx]: optionIdx,
    }));
  };

  const handleSubmitAnswer = () => {
    if (userAnswers[currentQuestionIdx] === undefined) return;
    setSubmittedQuestions((prev) => ({
      ...prev,
      [currentQuestionIdx]: true,
    }));
  };

  const handleNext = () => {
    if (!questions) return;
    if (currentQuestionIdx < questions.length - 1) {
      setCurrentQuestionIdx((prev) => prev + 1);
    } else {
      handleFinishQuiz();
    }
  };

  const handlePrev = () => {
    if (currentQuestionIdx > 0) {
      setCurrentQuestionIdx((prev) => prev - 1);
    }
  };

  const handleRestartQuiz = () => {
    setCurrentQuestionIdx(0);
    setUserAnswers({});
    setSubmittedQuestions({});
    setQuizCompleted(false);
    setMasteryResult(null);
  };

  // Parse questions
  let questions = [];
  if (currentQuiz) {
    if (Array.isArray(currentQuiz.questions) && currentQuiz.questions.length > 0) {
      questions = currentQuiz.questions;
    } else if (currentQuiz.questions_json) {
      try {
        questions =
          typeof currentQuiz.questions_json === 'string'
            ? JSON.parse(currentQuiz.questions_json)
            : currentQuiz.questions_json || [];
      } catch {
        questions = [];
      }
    }
  }

  // Calculate score
  let correctCount = 0;
  if (questions.length > 0) {
    questions.forEach((q, idx) => {
      if (userAnswers[idx] === q.correct_answer_index) {
        correctCount += 1;
      }
    });
  }
  const scorePercentage = questions.length > 0 ? Math.round((correctCount / questions.length) * 100) : 0;

  if (!selectedResource) {
    return (
      <Card className="text-center py-12 my-4">
        <div className="w-12 h-12 rounded-2xl bg-amber-100 dark:bg-amber-950 text-amber-600 dark:text-amber-400 mx-auto flex items-center justify-center mb-3">
          <HelpCircle className="w-6 h-6" />
        </div>
        <h3 className="text-base font-bold text-slate-800 dark:text-slate-200">
          Single Resource Required
        </h3>
        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 mb-4 max-w-md mx-auto">
          Practice Quiz generation requires selecting a single study resource. Please select a specific resource from the top picker.
        </p>
      </Card>
    );
  }

  return (
    <div className="space-y-4 my-4">
      {/* Quiz Configuration Controls Bar */}
      <Card className="p-4">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex flex-wrap items-center gap-4 text-xs font-semibold text-slate-700 dark:text-slate-300">
            <div className="flex items-center gap-2">
              <span className="uppercase text-[11px] text-slate-400">Questions:</span>
              <select
                value={questionCount}
                onChange={(e) => setQuestionCount(Number(e.target.value))}
                className="bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-lg p-1.5 focus:outline-none"
              >
                <option value={3}>3 Questions</option>
                <option value={5}>5 Questions</option>
                <option value={10}>10 Questions</option>
              </select>
            </div>

            <div className="flex items-center gap-2">
              <span className="uppercase text-[11px] text-slate-400">Difficulty:</span>
              <select
                value={difficulty}
                onChange={(e) => setDifficulty(e.target.value)}
                className="bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-lg p-1.5 focus:outline-none font-semibold text-blue-600 dark:text-blue-400"
              >
                <option value="easy">Easy</option>
                <option value="medium">Medium</option>
                <option value="hard">Hard</option>
              </select>
            </div>
          </div>

          <Button
            variant="primary"
            size="sm"
            icon={Sparkles}
            onClick={handleGenerate}
            isLoading={isGenerating}
            className="shadow-2xs"
          >
            Generate Quiz ({difficulty.toUpperCase()})
          </Button>
        </div>
      </Card>

      {/* Main Interactive Quiz Runner Content */}
      {isGenerating || isLoadingQuizzes ? (
        <Card className="p-8 space-y-4">
          <Skeleton className="h-4 w-32 mb-2" />
          <Skeleton className="h-6 w-full mb-6" />
          <Skeleton className="h-12 w-full" />
          <Skeleton className="h-12 w-full" />
          <Skeleton className="h-12 w-full" />
        </Card>
      ) : !currentQuiz || questions.length === 0 ? (
        <Card className="text-center py-12">
          <div className="w-12 h-12 rounded-2xl bg-blue-600/10 text-blue-400 border border-blue-500/20 mx-auto flex items-center justify-center mb-3">
            <Sparkles className="w-6 h-6" />
          </div>
          <h3 className="text-base font-bold text-[#f5f7fa]">
            No Quiz Available
          </h3>
          <p className="text-xs text-[#9ca8ba] mt-1 mb-6">
            Generate an interactive practice quiz for "{selectedResource.title || selectedResource.display_source}".
          </p>
          <Button variant="primary" size="md" icon={Sparkles} onClick={handleGenerate}>
            Generate Quiz
          </Button>
        </Card>
      ) : quizCompleted ? (
        /* Quiz Completion Final Score Screen */
        <Card className="max-w-lg mx-auto text-center p-8">
          <div className="w-16 h-16 rounded-3xl bg-blue-600/10 text-blue-400 border border-blue-500/20 mx-auto flex items-center justify-center mb-4 shadow-xs">
            <Award className="w-8 h-8" />
          </div>
          <h3 className="text-2xl font-extrabold text-[#f5f7fa]">
            Quiz Completed!
          </h3>
          <p className="text-xs text-[#9ca8ba] mt-1 mb-6">
            Review your score for "{selectedResource.title || selectedResource.display_source}".
          </p>

          <div className="bg-[#07090d] p-6 rounded-2xl border border-white/[0.07] mb-6">
            <div className="text-4xl font-extrabold text-blue-400 mb-1">
              {scorePercentage}%
            </div>
            <p className="text-xs font-semibold text-[#9ca8ba]">
              You answered {correctCount} out of {questions.length} questions correctly.
            </p>
          </div>

          <div className="flex justify-center gap-3">
            <Button variant="secondary" size="md" icon={RotateCcw} onClick={handleRestartQuiz}>
              Retry Quiz
            </Button>
            <Button variant="primary" size="md" icon={Sparkles} onClick={handleGenerate}>
              Generate New Quiz
            </Button>
          </div>
        </Card>
      ) : (
        /* Active Question Runner Card */
        <Card className="max-w-2xl mx-auto p-6 md:p-8">
          <div className="flex items-center justify-between mb-3 text-xs text-[#9ca8ba] font-semibold">
            <span>
              Question {currentQuestionIdx + 1} of {questions.length}
            </span>
            <Badge variant="primary" className="font-semibold">
              Practice Quiz
            </Badge>
          </div>

          <div className="w-full bg-[#07090d] h-2 rounded-full mb-6 overflow-hidden border border-white/[0.06]">
            <div
              className="bg-blue-600 h-full transition-all duration-300"
              style={{ width: `${((currentQuestionIdx + 1) / questions.length) * 100}%` }}
            />
          </div>

          <h3 className="text-base font-bold text-[#f5f7fa] mb-6">
            {questions[currentQuestionIdx]?.question}
          </h3>

          {/* Option Choices List */}
          <div className="space-y-3 mb-6">
            {questions[currentQuestionIdx]?.options.map((option, optIdx) => {
              const isSelected = userAnswers[currentQuestionIdx] === optIdx;
              const isSubmitted = submittedQuestions[currentQuestionIdx];
              const isCorrect = questions[currentQuestionIdx]?.correct_answer_index === optIdx;

              let optionStyle =
                'border-white/[0.08] bg-[#07090d]/60 text-[#f5f7fa] hover:border-blue-500/40';

              if (isSubmitted) {
                if (isCorrect) {
                  optionStyle =
                    'border-emerald-500 bg-emerald-500/15 text-emerald-200 font-semibold';
                } else if (isSelected) {
                  optionStyle =
                    'border-red-500 bg-red-500/15 text-red-200 font-semibold';
                } else {
                  optionStyle = 'border-white/[0.05] bg-[#07090d]/30 opacity-50';
                }
              } else if (isSelected) {
                optionStyle =
                  'border-blue-500 bg-blue-600/15 text-white font-semibold ring-1 ring-blue-500/30';
              }

              return (
                <div
                  key={optIdx}
                  onClick={() => handleSelectOption(optIdx)}
                  className={`p-4 rounded-xl border text-sm flex items-center justify-between cursor-pointer transition-all ${optionStyle}`}
                >
                  <div className="flex items-center gap-3">
                    <span className="w-6 h-6 rounded-full bg-white/[0.06] text-blue-400 font-bold text-xs flex items-center justify-center shrink-0 border border-white/[0.08]">
                      {String.fromCharCode(65 + optIdx)}
                    </span>
                    <span>{option}</span>
                  </div>

                  {isSubmitted && (
                    <div>
                      {isCorrect ? (
                        <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />
                      ) : isSelected ? (
                        <XCircle className="w-5 h-5 text-red-400 shrink-0" />
                      ) : null}
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {/* Explanation Box (Hidden until submitted) */}
          {submittedQuestions[currentQuestionIdx] && questions[currentQuestionIdx]?.explanation && (
            <div className="p-4 rounded-xl bg-[#07090d] border border-blue-500/30 mb-6 text-xs leading-relaxed">
              <span className="font-bold text-blue-400 block mb-1">
                Explanation:
              </span>
              <p className="text-[#9ca8ba]">
                {questions[currentQuestionIdx].explanation}
              </p>
            </div>
          )}

          {/* Question Footer Actions */}
          <div className="flex items-center justify-between pt-4 border-t border-slate-100 dark:border-slate-700/50">
            <Button
              variant="outline"
              size="sm"
              icon={ArrowLeft}
              onClick={handlePrev}
              disabled={currentQuestionIdx === 0}
            >
              Previous
            </Button>

            {!submittedQuestions[currentQuestionIdx] ? (
              <Button
                variant="primary"
                size="sm"
                onClick={handleSubmitAnswer}
                disabled={userAnswers[currentQuestionIdx] === undefined}
              >
                Submit Answer
              </Button>
            ) : (
              <Button variant="primary" size="sm" onClick={handleNext}>
                <span>
                  {currentQuestionIdx === questions.length - 1 ? 'Finish Quiz' : 'Next Question'}
                </span>
                <ArrowRight className="w-4 h-4 ml-1.5" />
              </Button>
            )}
          </div>
        </Card>
      )}
    </div>
  );
}
