import { Profile, Experience, Education, Skill, Project, Certification } from "@/types/profile";

export function validateProfile(profile: Profile): Record<string, string> {
  const errors: Record<string, string> = {};

  // Validate experience fields
  profile.experiences.forEach((exp: Experience, index: number) => {
    if (!exp.title?.trim()) {
      errors[`experiences[${index}].title`] = "Title is required";
    } else if (exp.title.length > 255) {
      errors[`experiences[${index}].title`] = "Title cannot exceed 255 characters";
    }

    if (!exp.company?.trim()) {
      errors[`experiences[${index}].company`] = "Company is required";
    } else if (exp.company.length > 255) {
      errors[`experiences[${index}].company`] = "Company cannot exceed 255 characters";
    }

    if (exp.location && exp.location.length > 255) {
      errors[`experiences[${index}].location`] = "Location cannot exceed 255 characters";
    }

    // Date validation
    if (exp.start_date && exp.end_date && new Date(exp.start_date) > new Date(exp.end_date)) {
      errors[`experiences[${index}].end_date`] = "End date cannot be before start date";
    }
  });

  // Validate education fields
  profile.educations.forEach((edu: Education, index: number) => {
    if (!edu.institution?.trim()) {
      errors[`educations[${index}].institution`] = "Institution is required";
    } else if (edu.institution.length > 255) {
      errors[`educations[${index}].institution`] = "Institution cannot exceed 255 characters";
    }

    if (edu.degree && edu.degree.length > 255) {
      errors[`educations[${index}].degree`] = "Degree cannot exceed 255 characters";
    }

    if (edu.field_of_study && edu.field_of_study.length > 255) {
      errors[`educations[${index}].field_of_study`] = "Field of study cannot exceed 255 characters";
    }

    // Date validation
    if (edu.start_date && edu.end_date && new Date(edu.start_date) > new Date(edu.end_date)) {
      errors[`educations[${index}].end_date`] = "End date cannot be before start date";
    }
  });

  // Validate skill fields
  profile.skills.forEach((skill: Skill, index: number) => {
    if (!skill.name?.trim()) {
      errors[`skills[${index}].name`] = "Skill name is required";
    } else if (skill.name.length > 100) {
      errors[`skills[${index}].name`] = "Skill name cannot exceed 100 characters";
    }

    if (skill.category && skill.category.length > 100) {
      errors[`skills[${index}].category`] = "Category cannot exceed 100 characters";
    }

    if (skill.proficiency && skill.proficiency.length > 50) {
      errors[`skills[${index}].proficiency`] = "Proficiency cannot exceed 50 characters";
    }
  });

  // Validate project fields
  profile.projects.forEach((project: Project, index: number) => {
    if (!project.name?.trim()) {
      errors[`projects[${index}].name`] = "Project name is required";
    } else if (project.name.length > 255) {
      errors[`projects[${index}].name`] = "Project name cannot exceed 255 characters";
    }

    if (project.url && project.url.length > 255) {
      errors[`projects[${index}].url`] = "URL cannot exceed 255 characters";
    }

    // Date validation
    if (
      project.start_date &&
      project.end_date &&
      new Date(project.start_date) > new Date(project.end_date)
    ) {
      errors[`projects[${index}].end_date`] = "End date cannot be before start date";
    }
  });

  // Validate certification fields
  profile.certifications.forEach((cert: Certification, index: number) => {
    if (!cert.name?.trim()) {
      errors[`certifications[${index}].name`] = "Certification name is required";
    } else if (cert.name.length > 255) {
      errors[`certifications[${index}].name`] = "Certification name cannot exceed 255 characters";
    }

    if (!cert.issuer?.trim()) {
      errors[`certifications[${index}].issuer`] = "Issuer is required";
    } else if (cert.issuer.length > 255) {
      errors[`certifications[${index}].issuer`] = "Issuer cannot exceed 255 characters";
    }

    if (cert.credential_id && cert.credential_id.length > 255) {
      errors[`certifications[${index}].credential_id`] =
        "Credential ID cannot exceed 255 characters";
    }

    if (cert.credential_url && cert.credential_url.length > 255) {
      errors[`certifications[${index}].credential_url`] =
        "Credential URL cannot exceed 255 characters";
    }

    // Date validation
    if (
      cert.issue_date &&
      cert.expiration_date &&
      new Date(cert.issue_date) > new Date(cert.expiration_date)
    ) {
      errors[`certifications[${index}].expiration_date`] =
        "Expiration date cannot be before issue date";
    }
  });

  // Validate profile fields
  if (profile.first_name && profile.first_name.length > 255) {
    errors.first_name = "First name cannot exceed 255 characters";
  }

  if (profile.last_name && profile.last_name.length > 255) {
    errors.last_name = "Last name cannot exceed 255 characters";
  }

  if (profile.headline && profile.headline.length > 255) {
    errors.headline = "Headline cannot exceed 255 characters";
  }

  if (profile.email && profile.email.length > 255) {
    errors.email = "Email cannot exceed 255 characters";
  }

  if (profile.phone && profile.phone.length > 50) {
    errors.phone = "Phone number cannot exceed 50 characters";
  }

  if (profile.location && profile.location.length > 255) {
    errors.location = "Location cannot exceed 255 characters";
  }

  if (profile.website && profile.website.length > 255) {
    errors.website = "Website cannot exceed 255 characters";
  }

  if (profile.linkedin && profile.linkedin.length > 255) {
    errors.linkedin = "LinkedIn URL cannot exceed 255 characters";
  }

  if (profile.github && profile.github.length > 255) {
    errors.github = "GitHub URL cannot exceed 255 characters";
  }

  return errors;
}

export function isValidUrl(string: string): boolean {
  try {
    new URL(string);
    return true;
  } catch (_) {
    return false;
  }
}

export function isValidEmail(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}

export function isValidPhone(phone: string): boolean {
  const phoneRegex = /^[\+]?[1-9][\d]{0,15}$/;
  return phoneRegex.test(phone.replace(/[\s\-\(\)]/g, ""));
}

export function isFutureDate(dateString: string): boolean {
  const date = new Date(dateString);
  const now = new Date();
  return date > now;
}

export function isPastDate(dateString: string): boolean {
  const date = new Date(dateString);
  const now = new Date();
  return date < now;
}
