import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { JobMatchScore } from "@/types/job";

interface MatchScoreCardProps {
  score: JobMatchScore;
}

export const MatchScoreCard: React.FC<MatchScoreCardProps> = ({ score }) => {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Match Score: {score.score}%</CardTitle>
      </CardHeader>
      <CardContent>
        <p>{score.explanation}</p>
        <div className="mt-4">
          <h4 className="font-semibold">Breakdown:</h4>
          <ul>
            {Object.entries(score.breakdown).map(([key, value]) => (
              <li key={key} className="flex justify-between">
                <span>{key}:</span>
                <span>{value}%</span>
              </li>
            ))}
          </ul>
        </div>
      </CardContent>
    </Card>
  );
};
